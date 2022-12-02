import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from tgbot.json.json_utils import advice_json, advice_keys
from tgbot.kb import dialogue_im, advice_rm, theory_im, main_rm, feedback_rm, chat_no_more_args_im, \
    about_project_im, ReplyMarkups
from tgbot.utils import FSMFeedback, send_feedback, get_facts, get_assertions
from tgbot.utils.util_classes import MessageText

mt = MessageText()


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(fsm_feedback, Text(equals='🤓 Оставить отзыв', ignore_case=True), state=None)
    dp.register_message_handler(fsm_feedback, commands=['feedback'], state=None)
    dp.register_message_handler(fsm_confirm_feedback, state=FSMFeedback.feedback)
    dp.register_message_handler(fsm_send_feedback, state=FSMFeedback.send_feedback)
    dp.register_message_handler(start_handler, commands=["start"], state="*")
    dp.register_message_handler(chat_mode, commands=["chat"], state="*")
    dp.register_message_handler(chat_mode, Text(equals='💬 Режим диалога', ignore_case=True), state="*")
    dp.register_message_handler(questions, Text(equals=[*get_assertions()], ignore_case=True),
                                # WARNING: Here's the problem with dynamic update
                                state="*")  # WARNING: SQL option
    dp.register_callback_query_handler(cb_more_args, text='more_arguments', state="*")
    dp.register_callback_query_handler(cb_feedback, text='feedback', state="*")
    dp.register_message_handler(practice_mode, commands=["practice"], state="*")
    dp.register_message_handler(practice_mode, Text(equals='🏋️‍♂ Симулятор разговора', ignore_case=True), state="*")
    dp.register_message_handler(advice_mode, commands=["advice"], state="*")
    dp.register_message_handler(advice_mode, Text(equals='🧠 Психология разговора', ignore_case=True), state="*")
    dp.register_message_handler(advice_mode2, Text(equals=[*advice_keys]), state="*")  # WARNING: JSON option
    dp.register_message_handler(theory_mode, commands=["theory"], state="*")
    dp.register_message_handler(theory_mode, Text(equals='📚 База аргументов', ignore_case=True), state="*")
    dp.register_message_handler(text_wasnt_found, state="*")
    dp.register_callback_query_handler(cb_home, text='main_menu', state="*")


def user_log(user_id, message_text):
    return logging.info(f'{user_id=} {message_text=}')


# def more_arguments(user_choice: dict): # WARNING: JSON option
#     # sourcery skip: inline-immediately-yielded-variable
#     for j in range(0, len(questions_answers_json[user_choice]), 3):
#         msg = '<b>Фраза-мост</b> ⬇\n' + questions_answers_json[user_choice][j] \
#               + '\n\n<b>Аргумент ⬇</b>\n' + questions_answers_json[user_choice][j + 1] \
#               + '\n\n<b>Наводящий вопрос ⬇</b>\n' + questions_answers_json[user_choice][j + 2]
#         yield msg


async def fsm_confirm_feedback(message: Message, state: FSMContext):
    if message.text in ['/start', '/chat', '/practice', '/advice', '/theory', '/feedback', '🤓 Оставить отзыв']:
        await message.answer('Написание отзыва отменено пользователем', reply_markup=main_rm)
        await state.finish()

    if message.text not in ['/start', '/chat', '/practice', '/advice', '/theory', '/feedback', '🤓 Оставить отзыв']:
        async with state.proxy() as data:
            data['user_feedback'] = message.text
        await  message.answer('Отправить отзыв?', reply_markup=feedback_rm)
        await FSMFeedback.next()


async def fsm_feedback(message: Message):
    await  message.answer(
        'Напишите отзыв о нашем проекте ⬇', reply_markup=ReplyKeyboardRemove())  # TODO: Cancel button!
    await FSMFeedback.feedback.set()  # state: feedback
    await message.delete()


async def fsm_send_feedback(message: Message, state: FSMContext):  # TODO: Checking message for text only type!
    if message.text == 'Отправить отзыв':
        user_id = message.from_user.id
        datetime = str(message.date)
        async with state.proxy() as data:
            send_feedback(user_id=user_id, datetime=datetime, feedback=data['user_feedback'])
        await message.answer('Спасибо, Ваш отзыв отправлен! 🤗', reply_markup=main_rm)
    else:
        await message.answer('Вы отменили отправку отзыва!', reply_markup=main_rm)
        await message.delete()
    await state.finish()


async def start_handler(message: Message):
    # user_id = message.from_user.id
    # user_full_name = message.from_user.full_name
    # logging.info(f'{user_id=} {user_full_name=}')
    user_log(message.from_user.id, message.text)

    await message.answer_photo(
        photo=open('tgbot/assets/menu.jpg', 'rb'),
        caption='Какое направление вы хотите запустить?', reply_markup=main_rm)
    await message.answer("💬 <b>Режим диалога</b>\n Подобрать подходящие аргументы.\n\n"
                         "🏋️‍♂ <b>Симулятор разговора</b>\n Подготовиться к реальному диалогу и проверить свои знания.\n\n"
                         "🧠 <b>Психология разговора</b>\n Узнать, как бережно говорить с близкими.\n\n"
                         "📚 <b>База аргументов</b>\n Прочитать все аргументы в одном месте.\n\n"
                         "🤓 <b>Оставить отзыв</b>\n Поделиться мнением о проекте.", reply_markup=about_project_im)
    await message.delete()


async def chat_mode(message: Message):
    await  message.answer_photo(
        photo=open('tgbot/assets/chat.jpg', 'rb'),
        caption='🟢 МОСТ работает в режиме диалога. Отправляйте фразу или вопрос в чат и получайте аргументы,'
                ' которые помогают отделить ложь от правды. Оценивайте их силу, чтобы сделать МОСТ еще крепче.',
        reply_markup=ReplyMarkups.questions_rm())
    await  message.answer('<i>Рассмотрим пример аргумента</i>\n\n'
                          'Собеседни_ца говорит вам: <b>«Мы многого не знаем, всё не так однозначно».</b>\n\n'
                          '<b>Фраза-мост — позволяет построить контакт с собеседником</b> ⬇\n'
                          'Соглашусь, что мы многого не знаем. Но мы точно знаем, что жизнь человека –'
                          ' высшая ценность общества, верно?\n\n'
                          '<b>Аргумент — конкретные примеры</b> ⬇\n'
                          'Я знаю одно: война несет смерть. Из-за войн страдают обычные люди.'
                          ' История научила нас этому, но почему-то мы думаем, что сможем провести войну без жертв.'
                          ' Так не бывает, к сожалению.\n\n'
                          '<b>Наводящий вопрос — продолжит диалог и запустит критическое мышление</b> ⬇\n'
                          'Что думаешь об этом?\n\n'
                          'Мы рекомендуем использовать три части ответа вместе, но по отдельности они тоже работают.\n\n'
                          'Выберите одну из предложенных тем ниже или введите свою в поле для ввода,'
                          ' чтобы получить аргумент. Например, «Путин знает, что делает» или «Это война с НАТО» ⬇')
    await message.delete()


async def questions(message: Message):  # These are callback-buttons!
    mt.set_message_text(message.text)
    # mt.set_message_text(more_arguments(mt.get_message_text())) # JSON option
    mt.set_message_text(get_facts(mt.get_message_text()))  # SQL option
    await  message.reply(next(mt.get_message_text()),
                         reply_markup=dialogue_im)  # WARNING: Dynamic arguments can't be recognized!


async def cb_more_args(call: CallbackQuery):
    try:
        await call.answer(cache_time=5)
        await call.message.answer(next(mt.get_message_text()), reply_markup=dialogue_im)
    except StopIteration:
        await  call.message.answer('Больше аргументов нет>', reply_markup=chat_no_more_args_im) # For testing purposes


async def practice_mode(message: Message):
    await  message.answer_photo(
        photo=open('tgbot/assets/practice.jpg', 'rb'),
        caption='🟢 МОСТ работает в режиме симулятор разговора.')
    await  message.answer('Проверьте, насколько хорошо вы умеете бороться с пропагандой.'
                          ' Мы собрали для вас 10 мифов о войне и для каждого подобрали 3 варианта ответа —'
                          ' выберите верные, а бот МОСТ даст подробные комментарии.',
                          reply_markup=ReplyKeyboardRemove())
    await message.delete()


async def advice_mode(message: Message):
    await  message.answer_photo(
        photo=open('tgbot/assets/advice.jpg', 'rb'),
        caption='🟢 Собрали советы психологов о том, как не сойти с ума и говорить о войне с близкими,'
                ' чего ожидать, как реагировать и вести себя.', reply_markup=ReplyKeyboardRemove())
    await  message.answer('Выберите тему, чтобы прочитать ⬇',
                          reply_markup=advice_rm)
    await message.delete()


async def advice_mode2(message: Message):
    for i in advice_json[message.text]: await message.answer(i, reply_markup=advice_rm)


async def theory_mode(message: Message):
    await message.answer('📚', reply_markup=ReplyKeyboardRemove())  # FIXME: This message is only for keyboard remove
    await  message.answer_photo(
        photo=open('tgbot/assets/theory.jpg', 'rb'),
        caption='Энциклопедия борца с пропагандой — самые полезные статьи, видео и аргументы.'
                ' Для тех, кто хочет детально разобраться в том, что происходит.',
        reply_markup=theory_im)
    await message.delete()


async def cb_home(call: CallbackQuery):
    await call.answer(cache_time=10)
    await start_handler(call.message)


async def cb_feedback(call: CallbackQuery):
    await call.answer(cache_time=10)
    await fsm_feedback(call.message)


async def text_wasnt_found(message: Message):
    await  message.answer(
        'Извините, я не смог распознать вопрос. Попробуйте еще раз или воспользуйтесь меню ниже ⬇',
        reply_markup=main_rm)