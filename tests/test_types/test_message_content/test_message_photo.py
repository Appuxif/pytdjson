from copy import deepcopy
from unittest import TestCase

from telegram.types.message_content import MessageContent, MessagePhoto

content_message_photo = {
    "@type": "messagePhoto",
    "photo": {
        "@type": "photo",
        "has_stickers": False,
        "minithumbnail": {
            "@type": "minithumbnail",
            "width": 40,
            "height": 28,
            "data": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDACgcHiMeGSgjISMtKygwPGRBPDc3PHtYXUlkkYCZlo+AjIqgtObDoKrarYqMyP/L2u71////m8H////6/+b9//j/2wBDASstLTw1PHZBQXb4pYyl+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj4+Pj/wAARCAAcACgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDVcOW+U4GPX/61Jtk9f1/+tUNzeR28oRg5YjPyjNPimEsYdd2D6imBIqv/ABMR9D/9anbD/fb9KZu+v5Uu4f7VIB4GB60U1SCe/wCNFAFTUgEgM+AxTGAeh5x/WshdSnSXcu0DOdnOK2NW/wCQfL9B/MVhW0SyPhvWncC3/bdx/wA84vyP+NKNan/55xfkf8apXUaxSYXOPeohSA62Ntyg+ozRSRfcX/dFFAH/2Q==",
        },
        "sizes": [
            {
                "@type": "photoSize",
                "type": "m",
                "photo": {
                    "@type": "file",
                    "id": 10179,
                    "size": 13106,
                    "expected_size": 13106,
                    "local": {
                        "@type": "localFile",
                        "path": "",
                        "can_be_downloaded": True,
                        "can_be_deleted": False,
                        "is_downloading_active": False,
                        "is_downloading_completed": False,
                        "download_offset": 0,
                        "downloaded_prefix_size": 0,
                        "downloaded_size": 0,
                    },
                    "remote": {
                        "@type": "remoteFile",
                        "id": "AgACAgIAAx0CZ4bt3AACDcxilxWhYfVilKJRelWamkOccfbW2wACFbkxGxZpuUjlMIFoqxiifwEAAwIAA20AAyIE",
                        "unique_id": "AQADFbkxGxZpuUhy",
                        "is_uploading_active": False,
                        "is_uploading_completed": True,
                        "uploaded_size": 13106,
                    },
                },
                "width": 320,
                "height": 229,
                "progressive_sizes": [],
            },
            {
                "@type": "photoSize",
                "type": "x",
                "photo": {
                    "@type": "file",
                    "id": 10180,
                    "size": 28815,
                    "expected_size": 28815,
                    "local": {
                        "@type": "localFile",
                        "path": "",
                        "can_be_downloaded": True,
                        "can_be_deleted": False,
                        "is_downloading_active": False,
                        "is_downloading_completed": False,
                        "download_offset": 0,
                        "downloaded_prefix_size": 0,
                        "downloaded_size": 0,
                    },
                    "remote": {
                        "@type": "remoteFile",
                        "id": "AgACAgIAAx0CZ4bt3AACDcxilxWhYfVilKJRelWamkOccfbW2wACFbkxGxZpuUjlMIFoqxiifwEAAwIAA3gAAyIE",
                        "unique_id": "AQADFbkxGxZpuUh9",
                        "is_uploading_active": False,
                        "is_uploading_completed": True,
                        "uploaded_size": 28815,
                    },
                },
                "width": 689,
                "height": 494,
                "progressive_sizes": [3165, 7059, 12390, 18119],
            },
        ],
    },
    "caption": {
        "@type": "formattedText",
        "text": "Fake formatted text",
        "entities": [
            {
                "@type": "textEntity",
                "offset": 0,
                "length": 4,
                "type": {"@type": "textEntityTypeBold"},
            },
            {
                "@type": "textEntity",
                "offset": 229,
                "length": 6,
                "type": {"@type": "textEntityTypeBold"},
            },
            {
                "@type": "textEntity",
                "offset": 296,
                "length": 15,
                "type": {
                    "@type": "textEntityTypeTextUrl",
                    "url": "https://www.railway.supply/vypusk-kassetnyh-podshipnikov-v-rossii-ostanovilsya/",
                },
            },
            {
                "@type": "textEntity",
                "offset": 526,
                "length": 7,
                "type": {
                    "@type": "textEntityTypeTextUrl",
                    "url": "https://aftershock.news/?q=node/1114259",
                },
            },
            {
                "@type": "textEntity",
                "offset": 735,
                "length": 8,
                "type": {
                    "@type": "textEntityTypeTextUrl",
                    "url": "https://mintrans.gov.ru/press-center/news/9256",
                },
            },
            {
                "@type": "textEntity",
                "offset": 933,
                "length": 7,
                "type": {
                    "@type": "textEntityTypeTextUrl",
                    "url": "https://gudok.ru/content/mechengineering/1602833/",
                },
            },
        ],
    },
    "is_secret": False,
}


class MessagePhotoTestCase(TestCase):
    """
    Тест кейс для объекта MessageAudio
    """

    def test(self, *args):
        """Проверка MessageAudio"""
        content_dict = deepcopy(content_message_photo)

        content = MessageContent(content_dict)

        self.assertIsInstance(content, MessagePhoto)
        self.assertEqual(content.caption.text, 'Fake formatted text')
        self.assertEqual(content.photo.has_stickers, False)
        self.assertEqual(content.photo.sizes[0].width, 320)
        self.assertEqual(content.photo.sizes[0].height, 229)
        self.assertEqual(content.photo.sizes[0].photo.size, 13106)
        self.assertEqual(len(content.photo.sizes), 2)
