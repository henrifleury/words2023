Игра в слова

    Бот пишет первое слово в чат. Генерируеутся последовательность, в которой игроки должны назвать слова.
    Бот указывает на пользователя, который в течении определенного времени должен назвать слово, которое начинается на последюю букву предыдущего слова.
    Игрок называет слово и бот должен проверить, что его раньше не было в текущей игровой сессии и оно действительно начинается на нужную букву.
    Большинство участников чата должны проголосовать, что названное слово - существует.
    За каждое успешно названное слово начисляются баллы.
    Игра длится до тех пор, пока не останется 1 игрок.

проект продолжается из решения задачи 3 недели курса kts по разработке асинхронных ботов
https://github.com/ktsstudio/hw-backend-summer-2022-3-sqlalchemy.git


Компоненты:
● Bot Daemon / Bot API — подсистема, слушающая события из VK (либо по Long-polling, либо по Callback API). Вся логика игровых сессий находится тут.
● Admin API — API для управления игрой (просмотр, модификация вопросов) и просмотра результатов.
● DB — Postgres SQL

MVP - в первом приближении можно играть
планировал продолжать, но на курсе kts произошли изменения и мы расстались. Спасибо им.


