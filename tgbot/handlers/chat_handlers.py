from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery

from tgbot.handlers import main_menu
from tgbot.kb import ReplyMarkups, InlineMarkups
from tgbot.utils import SQLRequests
from tgbot.utils.util_classes import MessageText, SectionName


def register_chat_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(chat_mode, commands=["chat"], state=None)
    dp.register_message_handler(chat_mode, Text(equals='💬 Режим диалога', ignore_case=True), state=None)
    dp.register_message_handler(assertions, Text(equals=SQLRequests
                                                 .select_by_table_and_column('assertions', 'assertion_name'),
                                                 ignore_case=True), state=None)
    dp.register_message_handler(a_questions, Text(equals=SQLRequests
                                                  .select_by_table_and_column('a_assertions', 'a_assertion_name'),
                                                  ignore_case=True), state=None)
    dp.register_callback_query_handler(thematic_questions, text='thematic_questions', state=None)
    dp.register_callback_query_handler(cb_more_args, text='more_arguments', state=None)
    dp.register_callback_query_handler(random_questions, text=['random_questions'], state=None)


async def chat_mode(message: Message) -> None:
    SectionName.s_name = 'Режим диалога'
    await  message.answer_photo(
        photo=open('tgbot/assets/chat.jpg', 'rb'),
        caption='🟢 МОСТ работает в режиме диалога. Отправляйте фразу или вопрос в чат и получайте аргументы,'
                ' которые помогают отделить ложь от правды. Оценивайте их силу, чтобы сделать МОСТ еще крепче.',
        reply_markup=ReplyMarkups.create_rm(2, True,
                                            *SQLRequests.select_by_table_and_column('assertions', 'assertion_name')))
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


# WARNING: Catch exception 'Message text is empty' (Admin has not added any facts yet)
async def assertions(message: Message) -> None:  # These are callback-buttons!
    MessageText.message_text = message.text
    MessageText.generator = SQLRequests.get_facts(MessageText.message_text)  # SQL option
    await  message.reply(next(MessageText.generator),
                         reply_markup=InlineMarkups.create_im(2, ['Еще аргумент', 'Другие вопросы', '👍', '👎',
                                                                  'Оставить отзыв', 'Главное меню'],
                                                              ['more_arguments', 'thematic_questions', 'some callback',
                                                               'some callback', 'feedback',
                                                               'main_menu']))


async def cb_more_args(call: CallbackQuery) -> None:
    try:
        await call.answer(cache_time=5)
        await call.message.answer(next(MessageText.generator),
                                  reply_markup=InlineMarkups.create_im(2, ['Еще аргумент', 'Другие вопросы', '👍', '👎',
                                                                           'Оставить отзыв', 'Главное меню'],
                                                                       ['more_arguments', 'thematic_questions',
                                                                        'some callback', 'some callback', 'feedback',
                                                                        'main_menu']))
    except StopIteration:
        if MessageText.message_text in SQLRequests.select_by_table_and_column('assertions', 'assertion_name'):
            await  call.message.answer('Хотите посмотреть дополнительные вопросы по теме?',
                                       reply_markup=InlineMarkups.
                                       create_im(2, ['Другие вопросы по теме', 'Главное меню'],
                                                 ['thematic_questions',
                                                  'main_menu']))
        elif MessageText.message_text in SQLRequests.select_by_table_and_column('a_assertions', 'a_assertion_name'):
            other_questions = ReplyMarkups.create_rm(2, True, *SQLRequests.rnd_questions())
            await call.message.answer('Вы можете выбрать другие вопросы из меню ниже:', reply_markup=other_questions)


async def thematic_questions(call: CallbackQuery) -> None:
    await call.answer(cache_time=5)
    await call.message.answer('Дополнительные вопросы, касающиеся данной темы ⬇',
                              reply_markup=ReplyMarkups.create_rm(2, True, *SQLRequests.get_assertions(
                                  MessageText.message_text)))


async def a_questions(message: Message) -> None:  # These are callback-buttons!
    MessageText.message_text = message.text
    MessageText.generator = SQLRequests.get_a_facts(MessageText.message_text)
    await  message.reply(next(MessageText.generator),
                         reply_markup=InlineMarkups.create_im(2, ['Еще аргумент', 'Другие вопросы', '👍', '👎',
                                                                  'Оставить отзыв', 'Главное меню'],
                                                              ['more_arguments', 'random_questions', 'some callback',
                                                               'some callback', 'feedback',
                                                               'main_menu']))  # WARNING: Dynamic arguments can't be recognized!


async def random_questions(call: CallbackQuery) -> None:
    await call.answer(cache_time=5)
    other_questions = ReplyMarkups.create_rm(2, True, *SQLRequests.rnd_questions())
    await call.message.answer('Вы можете выбрать другие вопросы из меню ниже:', reply_markup=other_questions)