PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    fio       TEXT    NOT NULL,
    phone     TEXT    NOT NULL,
    login     TEXT    NOT NULL UNIQUE,
    password  TEXT    NOT NULL,
    role      TEXT    NOT NULL
                CHECK(role IN (
                    'Администратор',
                    'Менеджер',
                    'Оператор',
                    'Специалист',
                    'Заказчик'
                ))
);

CREATE TABLE IF NOT EXISTS requests (
    request_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date          TEXT    NOT NULL,
    climate_tech_type   TEXT    NOT NULL,
    climate_tech_model  TEXT    NOT NULL,
    problem_description TEXT    NOT NULL,
    request_status      TEXT    NOT NULL DEFAULT 'Новая заявка'
                            CHECK(request_status IN (
                                'Новая заявка',
                                'В процессе ремонта',
                                'Ожидание комплектующих',
                                'Готова к выдаче',
                                'Завершена'
                            )),
    completion_date     TEXT,
    repair_parts        TEXT,
    master_id           INTEGER REFERENCES users(user_id),
    client_id           INTEGER NOT NULL REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    message    TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    master_id  INTEGER NOT NULL REFERENCES users(user_id),
    request_id INTEGER NOT NULL REFERENCES requests(request_id)
);

CREATE INDEX IF NOT EXISTS idx_requests_status
    ON requests(request_status);

CREATE INDEX IF NOT EXISTS idx_requests_client
    ON requests(client_id);

CREATE INDEX IF NOT EXISTS idx_requests_master
    ON requests(master_id);

CREATE INDEX IF NOT EXISTS idx_requests_start_date
    ON requests(start_date);

CREATE INDEX IF NOT EXISTS idx_comments_request
    ON comments(request_id);

INSERT INTO users (user_id, fio, phone, login, password, role) VALUES
(1,  'Широков Василий Матвеевич',       '89210563128', 'login1',  'pass1',  'Менеджер'),
(2,  'Кудрявцева Ева Ивановна',          '89535078985', 'login2',  'pass2',  'Специалист'),
(3,  'Гончарова Ульяна Ярославовна',     '89210673849', 'login3',  'pass3',  'Специалист'),
(4,  'Гусева Виктория Данииловна',       '89990563748', 'login4',  'pass4',  'Оператор'),
(5,  'Баранов Артём Юрьевич',            '89994563847', 'login5',  'pass5',  'Оператор'),
(6,  'Овчинников Фёдор Никитич',         '89219567849', 'login6',  'pass6',  'Заказчик'),
(7,  'Петров Никита Артёмович',          '89219567841', 'login7',  'pass7',  'Заказчик'),
(8,  'Ковалева Софья Владимировна',      '89219567842', 'login8',  'pass8',  'Заказчик'),
(9,  'Кузнецов Сергей Матвеевич',        '89219567843', 'login9',  'pass9',  'Заказчик'),
(10, 'Беспалова Екатерина Даниэльевна',  '89219567844', 'login10', 'pass10', 'Специалист'),
(11, 'Администратор Системы',            '00000000000', 'admin',   'admin',  'Администратор');

INSERT INTO requests
    (request_id, start_date, climate_tech_type, climate_tech_model,
     problem_description, request_status, completion_date,
     repair_parts, master_id, client_id)
VALUES
(1, '2023-06-06', 'Кондиционер',
    'TCL TAC-12CHSA/TPG-W белый',
    'Не охлаждает воздух',
    'В процессе ремонта', NULL, NULL, 2, 7),

(2, '2023-05-05', 'Кондиционер',
    'Electrolux EACS/I-09HAT/N3_21Y белый',
    'Выключается сам по себе',
    'В процессе ремонта', NULL, NULL, 3, 8),

(3, '2022-07-07', 'Увлажнитель воздуха',
    'Xiaomi Smart Humidifier 2',
    'Пар имеет неприятный запах',
    'Готова к выдаче', '2023-01-01', NULL, 3, 9),

(4, '2023-08-02', 'Увлажнитель воздуха',
    'Polaris PUH 2300 WIFI IQ Home',
    'Увлажнитель продолжает работать при предельном снижении уровня воды',
    'Новая заявка', NULL, NULL, NULL, 8),

(5, '2023-08-02', 'Сушилка для рук',
    'Ballu BAHD-1250',
    'Не работает',
    'Новая заявка', NULL, NULL, NULL, 9);

INSERT INTO comments (comment_id, message, master_id, request_id) VALUES
(1, 'Всё сделаем!',      2, 1),
(2, 'Всё сделаем!',      3, 2),
(3, 'Починим в момент.', 3, 3);

SELECT
    r.request_id        AS "№ заявки",
    r.start_date        AS "Дата создания",
    r.climate_tech_type AS "Тип оборудования",
    r.climate_tech_model AS "Модель",
    r.request_status    AS "Статус",
    r.completion_date   AS "Дата завершения",
    c.fio               AS "Заказчик",
    c.phone             AS "Телефон заказчика",
    m.fio               AS "Специалист"
FROM requests r
JOIN  users c ON r.client_id = c.user_id
LEFT JOIN users m ON r.master_id = m.user_id
ORDER BY r.start_date DESC;

SELECT
    request_status  AS "Статус",
    COUNT(*)        AS "Количество заявок",
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM requests), 1) AS "Доля (%)"
FROM requests
GROUP BY request_status
ORDER BY COUNT(*) DESC;

SELECT
    climate_tech_type   AS "Тип оборудования",
    COUNT(*)            AS "Количество заявок",
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM requests), 1) AS "Доля (%)",
    ROUND(AVG(
        CASE
            WHEN completion_date IS NOT NULL
            THEN julianday(completion_date) - julianday(start_date)
        END
    ), 1)               AS "Среднее время выполнения (дней)"
FROM requests
GROUP BY climate_tech_type
ORDER BY COUNT(*) DESC;

SELECT
    ROUND(AVG(julianday(completion_date) - julianday(start_date)), 1)
        AS "Среднее время выполнения (дней)",
    COUNT(*) AS "Количество завершённых заявок"
FROM requests
WHERE request_status = 'Завершена'
  AND completion_date IS NOT NULL;

SELECT
    u.fio           AS "Специалист",
    u.role          AS "Роль",
    COUNT(r.request_id) AS "Всего заявок",
    SUM(CASE WHEN r.request_status = 'Завершена' THEN 1 ELSE 0 END)
                    AS "Завершено"
FROM users u
LEFT JOIN requests r ON r.master_id = u.user_id
WHERE u.role IN ('Специалист', 'Менеджер')
GROUP BY u.user_id
ORDER BY COUNT(r.request_id) DESC;

SELECT
    r.request_id        AS "№ заявки",
    r.start_date        AS "Дата создания",
    r.climate_tech_type AS "Тип оборудования",
    r.request_status    AS "Статус",
    c.fio               AS "Заказчик"
FROM requests r
JOIN users c ON r.client_id = c.user_id
WHERE r.start_date BETWEEN '2023-01-01' AND '2023-12-31'
ORDER BY r.start_date;

SELECT
    c.comment_id    AS "№",
    r.request_id    AS "№ заявки",
    u.fio           AS "Автор",
    c.created_at    AS "Дата",
    c.message       AS "Комментарий"
FROM comments c
JOIN requests r ON c.request_id = r.request_id
JOIN users u    ON c.master_id  = u.user_id
ORDER BY c.request_id, c.created_at;

SELECT
    role        AS "Роль",
    COUNT(*)    AS "Количество пользователей",
    GROUP_CONCAT(fio, ', ') AS "Пользователи"
FROM users
GROUP BY role
ORDER BY
    CASE role
        WHEN 'Администратор' THEN 1
        WHEN 'Менеджер'      THEN 2
        WHEN 'Оператор'      THEN 3
        WHEN 'Специалист'    THEN 4
        WHEN 'Заказчик'      THEN 5
    END;

