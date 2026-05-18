# Java Coding Standards Template

> Project-agnostic Java coding standards. Customize per project via `context.yaml`.
> Markers: 【强制】= mandatory, 【推荐】= recommended

---

## 1. Naming Conventions

1. 【强制】Constants: `UPPER_SNAKE_CASE`, start with letter.
2. 【强制】Variables, fields, methods, parameters: `camelCase`, start with lowercase letter.
3. 【强制】Classes, interfaces, enums, annotations: `PascalCase`, start with uppercase letter.
4. 【强制】Packages: lowercase dot-separated, singular form (`user` not `users`).
5. 【强制】No offensive or discriminatory terms in code or comments.
6. 【强制】Avoid same names in parent/child member variables or local variables across blocks (except accessors/constructors).
7. 【强制】Boolean fields MUST NOT use `is` prefix — causes serialization issues across frameworks.
8. 【推荐】Identifiers must not use pinyin or mixed pinyin/English. Internationally recognized pinyin (e.g., `beijing`) acceptable.
9. 【推荐】No unexplained abbreviations. Use full words (`Abstract`, `Message`, `Return` — not `Abs`, `Msg`, `Ret`).
10. 【推荐】Type/unit suffix in constant/variable names: `MAX_ITEM_COUNT`, `TIMEOUT_SECOND`.
11. 【推荐】Method names use verb-object pattern: `getOptions`, `joinTeam`, `createUser`.
12. 【推荐】Abstract classes: `Abstract` or `Base` prefix. Exceptions: `Exception` suffix. Test classes: `<ClassUnderTest>Test`.

---

## 2. Code Formatting

1. 【强制】4-space indent, no tabs.
2. 【强制】Max line length: 120-150 characters (excluding imports/package).
3. 【强制】Max method length: 80 lines recommended, 150 lines hard limit.
4. 【强制】Max file length: 2000 lines.
5. 【强制】Max method parameters: 7. Use parameter objects or Builder pattern for more.
6. 【强制】UTF-8 encoding, Unix line endings (`\n`).
7. 【强制】No empty blocks in `if/else/switch/for/while/do/try/finally`.
8. 【强制】Brace style: opening brace on same line, closing brace on own line (except `else`).
9. 【强制】Space rules: space before `{`, no space inside `()`, space after `if/for/while/switch`, space around operators.
10. 【强制】No wildcard imports (`import java.util.*`). All imports explicit.
11. 【强制】No unused imports. No explicit imports of `java.lang.*` or same-package classes.
12. 【强制】Import order: `java`, `javax`, `org`, `com`, other — alphabetical within groups, static imports at group start.
13. 【推荐】Blank line between different logical sections of code.

---

## 3. Constants

1. 【强制】No magic values. All business-meaningful values must be named constants.
   - 正例: `MAX_HTTP_TIMEOUT_SECOND = 5`, `DEFAULT_PAGE_SIZE = 20`
   - 反例: `NUMBER_ZERO = 0` (just use `0` directly)
2. 【强制】Use uppercase `L` for long literals (`100L`, not `100l`).
3. 【推荐】Group constants by function, not one constants class for everything.
4. 【参考】Use `_` separator for long numbers: `1_000_000`.

---

## 4. Comments

1. 【强制】Public APIs use Javadoc (`/** */`). No `//` for public class/method docs.
2. 【强制】All classes must have author and creation date.
3. 【强制】Internal single-line comments: `//` on line above. Multi-line: `/* */`. Never `/** */` inside methods.
4. 【推荐】Update comments when changing code (parameters, return values, exceptions, core logic).
5. 【推荐】Delete unused fields, methods, inner classes. Delete unused parameters and local variables.
6. 【推荐】Don't comment out code — delete it. Use version control for history.
7. 【推荐】Prefer clear naming and structure over comments.
8. 【推荐】TODO/FIXME must include author and date. Clean up regularly.

---

## 5. Logging

1. 【强制】Use SLF4J facade. No `System.out`, `System.err`, `Throwable.printStackTrace()`.
2. 【强制】Use parameterized logging: `log.info("User {} logged in", userId)` — not string concatenation.
3. 【强制】No sensitive data (passwords, tokens, PII) in logs.
4. 【强制】No large JSON objects in logs (causes OOM). Log IDs/keys, not full objects.
5. 【推荐】Each log line should include: time, subject, event. Add context (business ID, user ID, IP).
6. 【推荐】High-volume logs: suppress stack traces, use rate-limited/sampled logging.
7. 【推荐】Complex sequential logic: use MDC for business trace correlation.
8. 【推荐】No `logger.isXxxEnabled()` guards unless the log point is extremely hot.

---

## 6. POJO Hierarchy

### Classification

| Type | Purpose | Lifecycle | equals/hashCode |
|------|---------|-----------|-----------------|
| Entity/DO | Persistent object, maps to DB table | Long | ID-based |
| Command | Business operation input | Short | All fields |
| Query | Query request parameters | Short | All fields |
| RO/Result | Non-entity query results | Short | All fields |
| Request | RPC/service request | Short | All fields |
| Response | RPC/service response | Short | All fields |
| VO | View/display layer output | Short | All fields |

### Rules

1. 【强制】No default values in POJO fields.
2. 【强制】No both `isXxx()` and `getXxx()` for same boolean field.
3. 【强制】All POJOs must override `toString()`. Override `hashCode()`/`equals()` when used as Map key or Set element.
4. 【强制】If field maps to DB column, ensure type matches.
5. 【推荐】Use IDE-generated `hashCode()`/`equals()`/`toString()`. Document any deviations.
6. 【推荐】Use explicit generic types, not `Object` or raw types.

---

## 7. Numeric and Currency

1. 【强制】Use `BigDecimal` for currency. Never `float` or `double`.
   - 反例: `double amount = 0.1 + 0.2;` → `0.30000000000000004`
   - 正例: `BigDecimal amount = new BigDecimal("0.1").add(new BigDecimal("0.2"));`
2. 【强制】Use `BigDecimal(String)` constructor, never `BigDecimal(double)`.
3. 【强制】Compare BigDecimal with `compareTo()`, not `equals()` (equals checks precision too).
4. 【强制】Integer wrapper comparison: always use `equals()`, never `==`.
5. 【强制】Float comparison: use range/delta, never `==` or `equals()`.
6. 【推荐】Store currency in smallest unit (cents) as integer when possible.

---

## 8. Collections and Streams

1. 【强制】Always use generic types. No raw collections.
2. 【强制】No `remove`/`add` in foreach loop. Use `Iterator.remove()` for deletion.
3. 【强制】`Map.keySet()`/`values()`/`entrySet()` — don't add elements to returned views.
4. 【强制】Collection to array: use `toArray(T[])` with zero-length array.
5. 【强制】Before `Collectors.toMap()`: filter null values to avoid NPE.
6. 【强制】No `parallelStream()` without custom `ForkJoinPool`.
7. 【推荐】Use `CollectionUtils.isEmpty()` for empty checks.
8. 【推荐】Use `EnumMap` for enum keys.
9. 【推荐】Specify initial capacity when size is known: `Lists.newArrayListWithExpectedSize(n)`.
10. 【推荐】Provide merge function in `Collectors.toMap()` to handle duplicate keys.

---

## 9. Concurrency

1. 【强制】Thread pools must have meaningful names for monitoring.
2. 【强制】No raw `Thread` creation — use thread pools.
3. 【强制】Use `ScheduledExecutorService`, not `java.util.Timer`.
4. 【强制】`ThreadLocal` must be `static`. Call `remove()` in `finally` block.
5. 【强制】No unbounded `Future.get()` — always specify timeout.
6. 【强制】Consistent lock ordering for multiple locks to prevent deadlocks.
7. 【推荐】Use `synchronized` by default; use Lock API only for advanced semantics (read-write lock, fair lock).
8. 【推荐】Minimize lock scope: code block > method, object lock > class lock.
9. 【推荐】Use `ThreadLocalRandom` instead of shared `Random` in multi-threaded code.
10. 【推荐】Use blocking queues instead of manual wait-notify for producer-consumer.

---

## 10. Exception Handling

1. 【强制】No empty catch blocks. Caught-and-ignored exceptions must have comment explaining why.
2. 【强制】Use try-with-resources for resource/Stream cleanup.
3. 【强制】No `return` in `finally` block (overrides try's return/throw).
4. 【强制】Don't catch `RuntimeException` that can be pre-checked (NPE, IndexOutOfBounds).
5. 【强制】Don't both log stack trace AND rethrow (causes duplicate output).
6. 【推荐】Business-expected exceptions: handle locally (Fail-Safe). Unexpected: rethrow (Fail-Fast).
7. 【推荐】Custom exceptions extend `RuntimeException` (unchecked). Avoid checked exceptions.
8. 【推荐】Don't throw raw `RuntimeException` — use specific exception types.

---

## 11. Forbidden Behaviors Checklist

| # | Behavior | Category | Impact |
|---|----------|----------|--------|
| 1 | Modify published migration files | Database | HIGH |
| 2 | Disable foreign key checks (`SET FOREIGN_KEY_CHECKS=0`) | Database | HIGH |
| 3 | Unnecessary indexes on hot tables | Database | MEDIUM |
| 4 | Schema design without scalability consideration | Database | MEDIUM |
| 5 | Cross-service calls without retry logic | Service | HIGH |
| 6 | Synchronous wait > 1s for remote calls | Service | HIGH |
| 7 | Ignore service degradation strategy | Service | HIGH |
| 8 | Inheritance chain > 3 levels | Quality | MEDIUM |
| 9 | Method > 30 lines without extraction | Quality | MEDIUM |
| 10 | Excessive global variables/singletons | Quality | MEDIUM |
| 11 | Hardcoded secrets/sensitive info | Security | HIGH |
| 12 | User input without validation | Security | HIGH |
| 13 | Log sensitive information | Security | MEDIUM |
| 14 | Float/double for financial calculations | Finance | CRITICAL |
| 15 | Deploy without running full test suite | Testing | HIGH |
| 16 | Test coverage < 80% | Testing | HIGH |
| 17 | Test cases missing exception scenarios | Testing | MEDIUM |

---

## 12. Pre-Coding Checklist

Before writing any code, verify:

- [ ] **Version constraints** documented (Java version, framework version, dependency versions, known incompatibilities)
- [ ] **Code reuse evaluated** — searched for existing similar functionality, documented reuse decision
- [ ] **CVE scan** — dependencies scanned, no critical/high CVEs, no hardcoded secrets
- [ ] **Special scenes identified** — financial/payment? security/auth? high-concurrency? Apply applicable rules
- [ ] **Test planning** — test cases planned (TDD preferred), coverage target >= 80%, happy + exception paths, integration tests for external calls

---

## 13. Testing Standards

1. 【推荐】AIR principle: **A**utomatic (non-interactive, assertion-based), **I**ndependent (no cross-test dependencies), **R**epeatable (no external state dependency).
2. 【推荐】Test behavior, not implementation. Verify outcomes, not internal calls.
3. 【推荐】One assertion per test when possible. Keep tests focused.
4. 【推荐】Clear test names describing the scenario: `testOrderProcessing_PaymentFailed`.
5. 【推荐】Deterministic tests — no timing dependency, no execution order dependency.
6. 【推荐】Cover happy path, exception path, and boundary conditions.
7. 【推荐】JUnit 5+ preferred. Test classes/methods don't need `public` — package-private is fine.
