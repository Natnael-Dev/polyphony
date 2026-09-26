# Pocketful SQLite Double-Entry Ledger Schema & Concurrency Blueprint

## Executive Architecture Summary
This document specifies the database architecture, schema DDL, mathematical conservation invariants, and high-concurrency configuration for the **Pocketful** service. Built for Go utilizing `modernc.org/sqlite` (pure Go, CGO-free), this blueprint guarantees absolute conservation of money, zero race conditions under 50+ concurrent requests, and strict adherence to double-entry accounting principles.

---

## 1. Concurrency Architecture & PRAGMA Settings

### 1.1 The SQLite Concurrency Model
SQLite operates as a single-writer, multi-reader database when Write-Ahead Logging (WAL) is active. In a multi-threaded Go application, multiple goroutines issuing concurrent write transactions against default SQLite settings will quickly encounter `SQLITE_BUSY (database is locked)` errors or upgrade deadlocks.

To maximize throughput and pass the harness burst tests (50 concurrent in-flight requests draining wallets), the Go service must configure both SQLite PRAGMAs and connection pool parameters.

### 1.2 Required Connection DSN & PRAGMAs

When opening the database connection in Go using `modernc.org/sqlite`:

```go
dsn := "file:/data/pocketful.db?" +
    "_pragma=journal_mode(WAL)&" +
    "_pragma=busy_timeout(5000)&" +
    "_pragma=synchronous(NORMAL)&" +
    "_pragma=foreign_keys(ON)&" +
    "_pragma=cache_size(-64000)&" +
    "_pragma=temp_store(MEMORY)"

db, err := sql.Open("sqlite", dsn)
```

| PRAGMA | Configured Value | Engineering Rationale |
|---|---|---|
| **`journal_mode`** | `WAL` | Write-Ahead Logging decouples readers from writers. Readers never block writers, and writers never block readers. |
| **`busy_timeout`** | `5000` | SQLite internal lock wait duration (5,000 ms). Eliminates transient `SQLITE_BUSY` errors under burst load by queuing write locks rather than aborting. |
| **`synchronous`** | `NORMAL` | In WAL mode, `NORMAL` is completely crash-safe and reduces disk syncs from 2 per transaction to 1 per checkpoint, increasing write throughput by up to 400%. |
| **`foreign_keys`** | `ON` | Enforces referential integrity between users, transactions, postings, and requests. |
| **`cache_size`** | `-64000` | Allocates 64 MB of RAM for in-memory page cache, ensuring hot tables and indexes stay memory-resident. |
| **`temp_store`** | `MEMORY` | Directs transient tables, sorting, and intermediate views to RAM rather than temporary disk files. |

### 1.3 Go Connection Pool & Lock Serialization Strategy

Even in WAL mode, SQLite permits **at most one active write transaction at a time**. If two goroutines begin a deferred transaction (`BEGIN DEFERRED`) with reads and subsequently attempt to write, both try to upgrade their read lock to a reserved lock, causing an unresolvable deadlock (`SQLITE_BUSY: database is locked`).

#### Recommended Go Concurrency Patterns:

1. **`BEGIN IMMEDIATE` on All Mutating Operations**:
   Every state-mutating transaction (payment, request pay, split, settlement, import, reset) must explicitly execute `BEGIN IMMEDIATE` (e.g. `tx, err := db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelSerializable})` or direct SQL `BEGIN IMMEDIATE`). This acquires the write lock at the very start of the transaction, ensuring clean FIFO queuing under `busy_timeout(5000)`.

2. **Dedicated Single Writer Pool or Mutex Guard**:
   To eliminate contention entirely at the application layer:
   ```go
   // SetMaxOpenConns(1) on a dedicated write DB handle, OR serialize writes with a sync.Mutex:
   type DBStore struct {
       db      *sql.DB
       writeMu sync.Mutex
   }
   ```
   Wrapping write transactions in `writeMu.Lock(); defer writeMu.Unlock()` guarantees that goroutines queue peacefully in Go runtime memory without hammering the OS-level SQLite lock file, yielding deterministic sub-millisecond dispatching.

---

## 2. Double-Entry Accounting Model & State Invariants

### 2.1 The Two Invariants

1. **Transaction Zero-Sum Invariant**:
   For every financial transaction $T$, the sum of all its postings must equal zero:
   $$\sum_{p \in T.\text{postings}} p.\text{amount} = 0$$
   A direct transfer of amount $A$ from User $X$ to User $Y$ produces:
   - Debit posting: Account $X$, amount $-A$
   - Credit posting: Account $Y$, amount $+A$
   - Sum: $(-A) + (+A) = 0$.

2. **Global Conservation of Money**:
   Across the entire system, the sum of all account balances after any sequence of valid operations equals the initial seeded total:
   $$\sum_{u \in \text{Users}} \text{balance}_u = \text{Seeded Total}$$
   Money is neither created nor destroyed. Deposits and withdrawals are out of scope.

3. **Strict Non-Negative Balance Rule**:
   $$\forall u \in \text{Users}, \quad \text{balance}_u \ge 0$$
   No wallet balance may drop below zero, even transiently.

### 2.2 Balance Enforcement Mechanisms

To guarantee that balances never drop below zero under high concurrency (e.g. 10 clients simultaneously attempting to transfer 1,000 minor units from a wallet that only holds 1,000):

#### Layer 1: SQLite Table Constraint
```sql
CREATE TABLE accounts (\
    user_id TEXT PRIMARY KEY,\
    balance INTEGER NOT NULL CHECK (balance >= 0),\
    updated_at TEXT NOT NULL,\
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE\
);
```
Any transaction that attempts to set `balance < 0` triggers an immediate constraint violation and rolls back cleanly.

#### Layer 2: Atomic Conditional UPDATE
```sql
UPDATE accounts 
SET balance = balance - :amount, updated_at = :now 
WHERE user_id = :from_user_id AND balance >= :amount;
```
In Go:
```go
res, err := tx.ExecContext(ctx, updateQuery, amount, now, fromUserID, amount)
if err != nil {
    return err
}
rows, err := res.RowsAffected()
if err != nil || rows == 0 {
    // Insufficient funds: balance was less than amount at time of execution
    return ErrInsufficientFunds // maps to 409 insufficient_funds
}
```
If 10 concurrent requests execute this query for Ada's 1,000 balance:
- The first transaction to acquire the write lock finds `balance == 1000 >= 1000`. Rows affected = 1. Balance becomes 0.
- The remaining 9 transactions execute after the balance is 0. `balance >= 1000` evaluates to FALSE. Rows affected = 0.
- Exactly 1 request succeeds with `201 Created`. Exactly 9 requests fail with `409 insufficient_funds`.

---

## 3. Production SQLite Schema (DDL)

```sql
-- ============================================================================
-- POCKETFUL STAGE 1 RECON SCHEMA
-- Pure Go SQLite (modernc.org/sqlite) Compatible
-- ============================================================================

-- Metadata table for system configuration and global parameters
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    handle TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_handle ON users(handle);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Active user bearer authentication sessions
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- Accounts / Wallets holding current balance
-- CHECK (balance >= 0) ensures negative balances are physically impossible in SQLite
CREATE TABLE IF NOT EXISTS accounts (
    user_id TEXT PRIMARY KEY,
    balance INTEGER NOT NULL CHECK (balance >= 0),
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Settlement operators table
CREATE TABLE IF NOT EXISTS settlement_operators (
    user_id TEXT PRIMARY KEY,
    granted_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- High-level financial transactions (Envelope)
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('payment', 'settlement', 'seed')),
    reference_id TEXT, -- payment_id or settlement_id
    created_at TEXT NOT NULL
);

-- Double-Entry Postings (Legs)
-- Sum of amount for a single transaction_id MUST equal 0
CREATE TABLE IF NOT EXISTS postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL,
    account_id TEXT NOT NULL, -- references accounts(user_id)
    amount INTEGER NOT NULL,  -- Negative for Debit, Positive for Credit
    created_at TEXT NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_postings_tx_id ON postings(transaction_id);
CREATE INDEX IF NOT EXISTS idx_postings_account_id ON postings(account_id);

-- Payments record (Activity Feed & Receipts)
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    from_user_id TEXT NOT NULL,
    from_handle TEXT NOT NULL,
    to_user_id TEXT NOT NULL,
    to_handle TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount >= 1 AND amount <= 1000000000),
    currency TEXT NOT NULL,
    note TEXT NOT NULL,
    visibility TEXT NOT NULL CHECK (visibility IN ('public', 'private')),
    request_id TEXT,
    settlement_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (from_user_id) REFERENCES users(id),
    FOREIGN KEY (to_user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_from_user ON payments(from_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_to_user ON payments(to_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_visibility ON payments(visibility, created_at DESC);

-- Requests record
CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    requester_id TEXT NOT NULL,
    requester_handle TEXT NOT NULL,
    payer_id TEXT NOT NULL,
    payer_handle TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount >= 1 AND amount <= 1000000000),
    currency TEXT NOT NULL,
    note TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'paid', 'declined', 'cancelled')),
    payment_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (requester_id) REFERENCES users(id),
    FOREIGN KEY (payer_id) REFERENCES users(id),
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);
CREATE INDEX IF NOT EXISTS idx_requests_payer ON requests(payer_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_requests_requester ON requests(requester_id, status, created_at DESC);

-- Splits record
CREATE TABLE IF NOT EXISTS splits (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users(id)
);

-- Split participant shares
CREATE TABLE IF NOT EXISTS split_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    split_id TEXT NOT NULL,
    handle TEXT NOT NULL,
    amount INTEGER NOT NULL,
    share_order INTEGER NOT NULL,
    FOREIGN KEY (split_id) REFERENCES splits(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_split_shares_split_id ON split_shares(split_id, share_order ASC);

-- Settlements record
CREATE TABLE IF NOT EXISTS settlements (
    id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL,
    committed_at TEXT NOT NULL,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

-- Idempotency tracking table
-- Scoped by user_id, method, path, and idempotency_key
CREATE TABLE IF NOT EXISTS idempotency_keys (
    user_id TEXT NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_status INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (user_id, method, path, key)
);
```

---

## 4. Invariant Verification in SQLite & Go

### 4.1 Zero-Sum Validation Trigger (Optional Safety Layer)
While Go validates $\sum \text{amount} = 0$ before committing, an immediate check trigger can be added:

```sql
CREATE TRIGGER IF NOT EXISTS trigger_verify_tx_zero_sum
AFTER INSERT ON postings
BEGIN
    SELECT RAISE(ABORT, 'double-entry invariant violated: transaction postings do not balance to zero')
    WHERE (
        SELECT COALESCE(SUM(amount), 0)
        FROM postings
        WHERE transaction_id = NEW.transaction_id
    ) != 0
    AND (
        -- Allow insertion of the first leg, but assert balance after second leg
        SELECT COUNT(*) FROM postings WHERE transaction_id = NEW.transaction_id
    ) >= 2;
END;
```

### 4.2 Application-Level Transaction Verification Pattern

In Go, every payment executes in an atomic transaction:

```go
func (s *Store) ExecutePayment(ctx context.Context, fromID, toID string, amount int64, payment Payment) (*Payment, error) {
    s.writeMu.Lock()
    defer s.writeMu.Unlock()

    tx, err := s.db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelSerializable})
    if err != nil {
        return nil, err
    }
    defer tx.Rollback()

    // 1. Debit sender conditionally (fails if balance < amount)
    res, err := tx.ExecContext(ctx, `
        UPDATE accounts 
        SET balance = balance - ?, updated_at = ? 
        WHERE user_id = ? AND balance >= ?`,
        amount, payment.CreatedAt, fromID, amount,
    )
    if err != nil {
        return nil, err
    }
    rows, _ := res.RowsAffected()
    if rows == 0 {
        return nil, ErrInsufficientFunds
    }

    // 2. Credit receiver
    _, err = tx.ExecContext(ctx, `
        UPDATE accounts 
        SET balance = balance + ?, updated_at = ? 
        WHERE user_id = ?`,
        amount, payment.CreatedAt, toID,
    )
    if err != nil {
        return nil, err
    }

    // 3. Insert transaction envelope
    txID := "tx_" + payment.ID
    _, err = tx.ExecContext(ctx, `
        INSERT INTO transactions (id, type, reference_id, created_at) 
        VALUES (?, 'payment', ?, ?)`,
        txID, payment.ID, payment.CreatedAt,
    )
    if err != nil {
        return nil, err
    }

    // 4. Insert balanced postings
    // Posting 1: Debit sender (-amount)
    _, err = tx.ExecContext(ctx, `
        INSERT INTO postings (transaction_id, account_id, amount, created_at) 
        VALUES (?, ?, ?, ?)`,
        txID, fromID, -amount, payment.CreatedAt,
    )
    if err != nil {
        return nil, err
    }

    // Posting 2: Credit receiver (+amount)
    _, err = tx.ExecContext(ctx, `
        INSERT INTO postings (transaction_id, account_id, amount, created_at) 
        VALUES (?, ?, ?, ?)`,
        txID, toID, amount, payment.CreatedAt,
    )
    if err != nil {
        return nil, err
    }

    // 5. Insert payment record
    _, err = tx.ExecContext(ctx, `
        INSERT INTO payments (id, from_user_id, from_handle, to_user_id, to_handle, amount, currency, note, visibility, request_id, settlement_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        payment.ID, payment.FromUserID, payment.FromHandle, payment.ToUserID, payment.ToHandle,
        payment.Amount, payment.Currency, payment.Note, payment.Visibility, payment.RequestID, payment.SettlementID, payment.CreatedAt,
    )
    if err != nil {
        return nil, err
    }

    // 6. Commit atomic transaction
    if err := tx.Commit(); err != nil {
        return nil, err
    }

    return &payment, nil
}
```

This pattern guarantees:
- Atomic application of debit and credit.
- Immediate rollback on insufficient funds with zero state alteration.
- Balanced double-entry postings stored in the immutable audit ledger.
- Safe serialization avoiding any SQLite lock collisions under high concurrency.
