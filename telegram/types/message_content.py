from dataclasses import dataclass
from typing import List

from telegram.types.base import ObjectBuilder, RawDataclass
from telegram.types.common import Contact, Location, ProductInfo, Venue
from telegram.types.files import (
    AlternativeVideoFile,
    AnimationFile,
    AudioFile,
    DocumentFile,
    PhotoFile,
    VideoFile,
    VideoNote,
    VideoStoryboardFile,
    VoiceNote,
)
from telegram.types.message_sender import MessageSender
from telegram.types.poll import Poll
from telegram.types.text import FormattedText


@dataclass
class MessageContentBase(RawDataclass):
    """Базовый класс контента сообщения"""


@dataclass
class MessageText(MessageContentBase):
    """Текстовое сообщение"""

    text: FormattedText = None
    # link_preview:linkPreview = None
    # link_preview_options: linkPreviewOptions


@dataclass
class MessageAnimation(MessageContentBase):
    """Анимация"""

    animation: AnimationFile = None
    caption: FormattedText = None
    # show_caption_above_media:Bool
    has_spoiler: bool = None
    is_secret: bool = None


@dataclass
class MessageAudio(MessageContentBase):
    """Аудио"""

    audio: AudioFile = None
    caption: FormattedText = None


@dataclass
class MessageDocument(MessageContentBase):
    """Документ"""

    document: DocumentFile = None
    caption: FormattedText = None


@dataclass
class MessagePaidMedia(MessageContentBase):
    """messagePaidMedia"""

    star_count: int = None
    # media:vector<PaidMedia>
    caption: FormattedText = None
    show_caption_above_media: bool = None


@dataclass
class MessagePhoto(MessageContentBase):
    """Фото"""

    photo: PhotoFile = None
    caption: FormattedText = None
    show_caption_above_media: bool = None
    has_spoiler: bool = None
    is_secret: bool = None


@dataclass
class MessageSticker(MessageContentBase):
    # sticker: sticker = None
    is_premium: bool = None


@dataclass
class MessageVideo(MessageContentBase):
    """Сообщение-видео"""

    video: VideoFile = None
    alternative_videos: List[AlternativeVideoFile] = None
    storyboards: List[VideoStoryboardFile] = None
    # cover:photo
    start_timestamp: int = None
    caption: FormattedText = None
    show_caption_above_media: bool = None
    has_spoiler: bool = None
    is_secret: bool = False


@dataclass
class MessageVideoNote(MessageContentBase):
    """Видео-Заметка"""

    video_note: VideoNote = None
    is_viewed: bool = False
    is_secret: bool = False


@dataclass
class MessageVoiceNote(MessageContentBase):
    """Голосовое сообщение"""

    voice_note: VoiceNote = None
    caption: FormattedText = None
    is_listened: bool = False


@dataclass
class MessageExpiredPhoto(MessageContentBase):
    """MessageExpiredPhoto"""


@dataclass
class MessageExpiredVideo(MessageContentBase):
    """MessageExpiredVideo"""


@dataclass
class MessageExpiredVideoNote(MessageContentBase):
    """MessageExpiredVideoNote"""


@dataclass
class MessageExpiredVoiceNote(MessageContentBase):
    """messageExpiredVoiceNote"""


@dataclass
class MessageLocation(MessageContentBase):
    """Локация"""

    location: Location = None
    live_period: int = None
    expires_in: int = None
    heading: int = None
    proximity_alert_radius: int = None


@dataclass
class MessageVenue(MessageContentBase):
    """Место сбора"""

    venue: Venue = None


@dataclass
class MessageContact(MessageContentBase):
    """Контакт"""

    contact = Contact


@dataclass
class MessageAnimatedEmoji(MessageContentBase):
    """messageAnimatedEmoji"""

    # animated_emoji:animatedEmoji
    emoji: str = None


@dataclass
class MessageDice(MessageContentBase):
    """messageDice"""

    # initial_state: DiceStickers = None
    # final_state: DiceStickers = None
    emoji: str = None
    value: int = None
    success_animation_frame_number: int = None


@dataclass
class MessageGame(MessageContentBase):
    """messageGame"""

    # game:game = None


@dataclass
class MessagePoll(MessageContentBase):
    """Опрос"""

    poll: Poll = None


@dataclass
class MessageStory(MessageContentBase):
    """messageStory"""

    story_poster_chat_id: int = None
    story_id: int = None
    via_mention: bool = None


@dataclass
class MessageChecklist(MessageContentBase):
    """messageChecklist"""

    # list:checklist


@dataclass
class MessageInvoice(MessageContentBase):
    """Чек"""

    product_info: ProductInfo = None
    currency: str = None
    total_amount: int = None
    start_parameter: str = None
    is_test: bool = None
    need_shipping_address: bool = None
    receipt_message_id: int = None
    # paid_media:PaidMedia
    paid_media_caption: FormattedText = None


@dataclass
class MessageCall(MessageContentBase):
    """messageCall"""

    is_video: bool = None
    # discard_reason:CallDiscardReason
    duration: int = None


@dataclass
class MessageGroupCall(MessageContentBase):
    """messageGroupCall"""

    is_active: bool = None
    was_missed: bool = None
    is_video: bool = None
    duration: int = None
    other_participant_ids: List[MessageSender] = None


@dataclass
class MessageVideoChatScheduled(MessageContentBase):
    """messageVideoChatScheduled"""

    group_call_id: int = None
    start_date: int = None


@dataclass
class MessageVideoChatStarted(MessageContentBase):
    """messageVideoChatStarted"""

    group_call_id: int = None


@dataclass
class MessageVideoChatEnded(MessageContentBase):
    """messageVideoChatEnded"""

    duration: int = None


@dataclass
class MessageVideoChatScheduled(MessageContentBase):
    """messageVideoChatScheduled"""

    group_call_id: int = None
    start_date: int = None


@dataclass
class MessageUnsupported(MessageContentBase):
    """Сообщение не поддерживается"""


@dataclass
class MessageChatAddMembers(MessageContentBase):
    """Место сбора"""

    member_user_ids: list = None


class MessageContentBuilder(ObjectBuilder):
    """Билдер, возвращает один из MessageContent"""

    def __init__(self):
        super().__init__()
        self.mapping = {}
        for cls in MessageContentBase.__subclasses__():
            key = cls.__name__
            key = key[0].lower() + key[1:]
            self.mapping[key] = cls


MessageContent = MessageContentBuilder()
