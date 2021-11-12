from dataclasses import dataclass
from enum import Enum


class TextParseModeTypes(Enum):
    """Типы парсинга текстов через tdlib"""

    HTML = {'@type': 'textParseModeHTML'}
    MARKDOWN = {'@type': 'textParseModeMarkdown', 'version': 2}


# class MessageContentType(Enum):
#     """Типы контента сообщений"""
#
#     ANIMATION = 'messageAnimation'
#     AUDIO = 'messageAudio'
#     BASIC_GROUP_CHAT_CREATE = 'messageBasicGroupChatCreate'
#     CALL = 'messageCall'
#     CHAT_ADD_MEMBERS = 'messageChatAddMembers'
#     CHAT_CHANGE_PHOTO = 'messageChatChangePhoto'
#     CHAT_CHANGE_TITLE = 'messageChatChangeTitle'
#     CHAT_DELETE_MEMBER = 'messageChatDeleteMember'
#     CHAT_DELETE_PHOTO = 'messageChatDeletePhoto'
#     CHAT_JOIN_BY_LINK = 'messageChatJoinByLink'
#     CHAT_SET_TTL = 'messageChatSetTtl'
#     CHAT_UPGRADE_FROM = 'messageChatUpgradeFrom'
#     CHAT_UPGRADE_TO = 'messageChatUpgradeTo'
#     CONTACT = 'messageContact'
#     CONTACT_REGISTERED = 'messageContactRegistered'
#     CUSTOM_SERVICE_ACTION = 'messageCustomServiceAction'
#     DICE = 'messageDice'
#     DOCUMENT = 'messageDocument'
#     EXPIRED_PHOTO = 'messageExpiredPhoto'
#     EXPIRED_VIDEO = 'messageExpiredVideo'
#     GAME = 'messageGame'
#     GAME_SCORE = 'messageGameScore'
#     INVOICE = 'messageInvoice'
#     LOCATION = 'messageLocation'
#     PASSPORT_DATA_RECEIVED = 'messagePassportDataReceived'
#     PASSPORT_DATA_SENT = 'messagePassportDataSent'
#     PAYMENT_SUCCESSFUL = 'messagePaymentSuccessful'
#     PAYMENT_SUCCESSFUL_BOT = 'messagePaymentSuccessfulBot'
#     PHOTO = 'messagePhoto'
#     PIN_MESSAGE = 'messagePinMessage'
#     POLL = 'messagePoll'
#     PROXIMITY_ALERT_TRIGGERED = 'messageProximityAlertTriggered'
#     SCREENSHOT_TAKEN = 'messageScreenshotTaken'
#     STICKER = 'messageSticker'
#     SUPERGROUP_CHAT_CREATE = 'messageSupergroupChatCreate'
#     TEXT = 'messageText'
#     UNSUPPORTED = 'messageUnsupported'
#     VENUE = 'messageVenue'
#     VIDEO = 'messageVideo'
#     VIDEO_NOTE = 'messageVideoNote'
#     VOICE_NOTE = 'messageVoiceNote'
#     WEBSITE_CONNECTED = 'messageWebsiteConnected'
#
#     IGNORED = (
#         BASIC_GROUP_CHAT_CREATE,
#         CALL,
#         CHAT_CHANGE_PHOTO,
#         CHAT_CHANGE_TITLE,
#         CHAT_DELETE_PHOTO,
#         CHAT_SET_TTL,
#         CHAT_UPGRADE_FROM,
#         CHAT_UPGRADE_TO,
#         CONTACT,
#         CONTACT_REGISTERED,
#         CUSTOM_SERVICE_ACTION,
#         DICE,
#         EXPIRED_PHOTO,
#         EXPIRED_VIDEO,
#         GAME,
#         GAME_SCORE,
#         PASSPORT_DATA_RECEIVED,
#         PASSPORT_DATA_SENT,
#         PAYMENT_SUCCESSFUL,
#         PAYMENT_SUCCESSFUL_BOT,
#         PIN_MESSAGE,
#         PROXIMITY_ALERT_TRIGGERED,
#         SCREENSHOT_TAKEN,
#         SUPERGROUP_CHAT_CREATE,
#     )
#
#
# class MessageSenderType(Enum):
#     """Типы отправителей сообщения"""
#
#     CHAT = 0
#     USER = 1
#
#
# @dataclass
# class MessageSender:
#     id: int
#     type: MessageSenderType
#
#
# @dataclass
# class ForwardInfo:
#     """Информация об внутреннем отправителе сообщения"""
#
#     date: int
#     from_chat_id: int
#     from_message_id: int
#
#
# class TextEntityType(Enum):
#     """Типы элементов форматирования текста"""
#
#     BANK_CARD_NUMBER = 'textEntityTypeBankCardNumber'
#     BOLD = 'textEntityTypeBold'
#     BOT_COMMAND = 'textEntityTypeBotCommand'
#     CASHTAG = 'textEntityTypeCashtag'
#     CODE = 'textEntityTypeCode'
#     EMAIL_ADDRESS = 'textEntityTypeEmailAddress'
#     HASHTAG = 'textEntityTypeHashtag'
#     ITALIC = 'textEntityTypeItalic'
#     MENTION = 'textEntityTypeMention'
#     MENTION_NAME = 'textEntityTypeMentionName'
#     PHONE_NUMBER = 'textEntityTypePhoneNumber'
#     PRE = 'textEntityTypePre'
#     PRE_CODE = 'textEntityTypePreCode'
#     STRIKETHROUGH = 'textEntityTypeStrikethrough'
#     TEXT_URL = 'textEntityTypeTextUrl'
#     UNDERLINE = 'textEntityTypeUnderline'
#     URL = 'textEntityTypeUrl'
#
#
# @dataclass
# class TextEntity:
#     """Элемент форматирования текста"""
#
#     offset: int
#     length: int
#     type: TextEntityType
#     data: str
#
#
# @dataclass
# class FormattedText:
#     """Форматированный текст"""
#
#     text: str
#     entities: [TextEntity]


@dataclass(frozen=True)
class Message:
    """Сообщение из обновления телеграм"""

    # id: int
    # chat_id: int
    # type: MessageContentType
    #
    # message_sender: MessageSender
    # date: int
    #
    # is_outgoing: bool
    # is_pinned: bool
    # can_be_edited: bool
    # can_be_forwarded: bool
    # can_be_deleted_only_for_self: bool
    # can_be_deleted_for_all_users: bool
    # can_get_statistics: bool
    # is_channel_post: bool
    # contains_unread_mention: bool
    # edit_date: bool
    #
    # forward_info: ForwardInfo
    #
    # caption: FormattedText = None
    # text: FormattedText = None
    # new_member_ids: list = None
    # delete_member_id: int = None
    #
    # # animation: Animation = None
    # # audio: Audio = None
    # # contact: Contact = None
    # TODO: Fill the content types fields

    @classmethod
    def build(cls, message: dict) -> 'Message':
        pass
        # _type = message.pop('@type')
        # return cls(type=_type, **message)


build_message = Message.build
