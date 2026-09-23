from unittest import TestCase

from telegram.mcp import projection


class ProjectionTestCase(TestCase):
    def test_message_keeps_only_compact_content(self):
        result = projection.message(
            {
                'id': 2,
                'chat_id': 1,
                'sender_id': {'@type': 'messageSenderUser', 'user_id': 3},
                'date': 4,
                'content': {
                    '@type': 'messageText',
                    'text': {'text': 'hello', 'entities': [{'ignored': True}]},
                },
                'reply_markup': {'secret': 'not returned'},
            }
        )

        self.assertEqual('hello', result['text'])
        self.assertEqual({'type': 'messageSenderUser', 'user_id': 3}, result['sender'])
        self.assertNotIn('reply_markup', result)

    def test_message_preserves_topic_and_reply_metadata(self):
        result = projection.message(
            {
                'id': 2,
                'chat_id': 1,
                'sender_id': {'@type': 'messageSenderUser', 'user_id': 3},
                'topic_id': {
                    '@type': 'messageTopicForum',
                    'forum_topic_id': 7,
                },
                'reply_to': {
                    '@type': 'messageReplyToMessage',
                    'chat_id': 1,
                    'message_id': 6,
                },
                'content': {'@type': 'messageText', 'text': {'text': 'hello'}},
            }
        )

        self.assertEqual(
            {'type': 'messageTopicForum', 'forum_topic_id': 7},
            result['topic_id'],
        )
        self.assertEqual(
            {'type': 'messageReplyToMessage', 'chat_id': 1, 'message_id': 6},
            result['reply_to'],
        )

    def test_message_exposes_sticker_as_emoji_without_file_data(self):
        result = projection.message(
            {
                'id': 2,
                'chat_id': 1,
                'content': {
                    '@type': 'messageSticker',
                    'is_premium': True,
                    'sticker': {
                        'id': 123,
                        'set_id': 456,
                        'emoji': '😂',
                        'sticker': {'id': 789},
                    },
                },
            }
        )

        self.assertEqual('😂', result['text'])
        self.assertEqual('😂', result['sticker_emoji'])
        self.assertEqual(123, result['sticker_id'])
        self.assertEqual(456, result['sticker_set_id'])
        self.assertTrue(result['sticker_is_premium'])
        self.assertNotIn('sticker', result)

    def test_message_exposes_compact_media_interaction_and_entities(self):
        result = projection.message(
            {
                'id': 2,
                'chat_id': 1,
                'interaction_info': {
                    'view_count': 4,
                    'forward_count': 2,
                    'reply_info': {'reply_count': 3, 'last_message_id': 9},
                    'reactions': {
                        'reactions': [
                            {
                                'type': {'@type': 'reactionTypeEmoji', 'emoji': '👍'},
                                'total_count': 2,
                                'is_chosen': True,
                            }
                        ]
                    },
                },
                'content': {
                    '@type': 'messageAudio',
                    'caption': {
                        'text': 'voice',
                        'entities': [{'@type': 'textEntityTypeBold'}],
                    },
                    'audio': {
                        'duration': 4,
                        'mime_type': 'audio/ogg',
                        'file_name': 'voice.ogg',
                        'audio': {
                            'id': 17,
                            'size': 8,
                            'local': {'path': '/tmp/voice.ogg'},
                            'remote': {'id': 'remote-17'},
                        },
                    },
                },
            }
        )

        self.assertEqual('voice', result['text'])
        self.assertEqual('audio/ogg', result['media']['mime_type'])
        self.assertEqual(17, result['media']['file']['id'])
        self.assertEqual([{'@type': 'textEntityTypeBold'}], result['entities'])
        self.assertEqual(4, result['interaction']['view_count'])
        self.assertEqual('👍', result['interaction']['reactions'][0]['emoji'])

    def test_reaction_results_are_projected_without_media_payloads(self):
        available = projection.available_reactions(
            {
                'top_reactions': [
                    {
                        'type': {
                            '@type': 'reactionTypeEmoji',
                            'emoji': '👍',
                        },
                        'needs_premium': False,
                    },
                    {
                        'type': {
                            '@type': 'reactionTypeCustomEmoji',
                            'custom_emoji_id': 123,
                        },
                        'needs_premium': True,
                    },
                ],
                'recent_reactions': [],
                'popular_reactions': [],
                'allow_custom_emoji': True,
                'are_tags': False,
                'unavailability_reason': None,
            }
        )
        added = projection.added_reactions(
            {
                'total_count': 1,
                'reactions': [
                    {
                        'type': {
                            '@type': 'reactionTypeEmoji',
                            'emoji': '👍',
                        },
                        'sender_id': {
                            '@type': 'messageSenderUser',
                            'user_id': 7,
                        },
                        'is_outgoing': True,
                        'date': 123,
                    }
                ],
                'next_offset': 'next',
            }
        )

        self.assertEqual(
            {
                'type': 'reactionTypeEmoji',
                'emoji': '👍',
            },
            available['top_reactions'][0]['reaction'],
        )
        self.assertEqual(
            123, available['top_reactions'][1]['reaction']['custom_emoji_id']
        )
        self.assertEqual(
            {
                'type': 'messageSenderUser',
                'user_id': 7,
            },
            added['reactions'][0]['sender'],
        )
        self.assertEqual('next', added['next_offset'])

    def test_reaction_update_events_preserve_changed_reaction_details(self):
        interaction = projection.update(
            {
                '@type': 'updateMessageInteractionInfo',
                'chat_id': 10,
                'message_id': 20,
                'interaction_info': {
                    'view_count': 4,
                    'reactions': {
                        'reactions': [
                            {
                                'type': {
                                    '@type': 'reactionTypeEmoji',
                                    'emoji': '👍',
                                },
                                'total_count': 3,
                                'is_chosen': True,
                            }
                        ]
                    },
                },
            }
        )
        reaction = projection.update(
            {
                '@type': 'updateMessageReaction',
                'chat_id': 10,
                'message_id': 20,
                'actor_id': {'@type': 'messageSenderUser', 'user_id': 30},
                'old_reaction_types': [{'@type': 'reactionTypeEmoji', 'emoji': '👎'}],
                'new_reaction_types': [{'@type': 'reactionTypeEmoji', 'emoji': '👍'}],
            }
        )

        self.assertEqual(4, interaction['interaction_info']['view_count'])
        self.assertEqual(
            3, interaction['interaction_info']['reactions'][0]['total_count']
        )
        self.assertEqual(
            {'type': 'messageSenderUser', 'user_id': 30}, reaction['actor_id']
        )
        self.assertEqual('👎', reaction['old_reaction_types'][0]['emoji'])
        self.assertEqual('👍', reaction['new_reaction_types'][0]['emoji'])

    def test_message_content_update_projects_replacement_text_and_media(self):
        text_update = projection.update(
            {
                '@type': 'updateMessageContent',
                'chat_id': 10,
                'message_id': 20,
                'new_content': {
                    '@type': 'messageText',
                    'text': {'text': 'replacement text'},
                },
            }
        )
        media_update = projection.update(
            {
                '@type': 'updateMessageContent',
                'chat_id': 10,
                'message_id': 20,
                'new_content': {
                    '@type': 'messageVideo',
                    'video': {
                        'duration': 6,
                        'video': {'id': 91, 'size': 123},
                    },
                },
            }
        )

        self.assertEqual('messageText', text_update['new_content']['content_type'])
        self.assertEqual('replacement text', text_update['new_content']['text'])
        self.assertEqual('messageVideo', media_update['new_content']['content_type'])
        self.assertEqual(91, media_update['new_content']['media']['file']['id'])

    def test_message_transcription_update_keeps_original_message_metadata(self):
        result = projection.update(
            {
                '@type': 'mcpMessageTranscription',
                'chat_id': 1,
                'message_id': 2,
                'status': 'completed',
                'text': 'hello from audio',
                'original_message': {
                    'id': 2,
                    'chat_id': 1,
                    'sender_id': {
                        '@type': 'messageSenderUser',
                        'user_id': 3,
                    },
                    'content': {'@type': 'messageVoiceNote'},
                },
            }
        )

        self.assertEqual('message_transcription', result['type'])
        self.assertEqual('completed', result['status'])
        self.assertEqual('hello from audio', result['text'])
        self.assertEqual(2, result['original_message']['id'])
        self.assertEqual('messageVoiceNote', result['original_message']['content_type'])

    def test_forum_topics_projection_keeps_topic_identity_and_cursor(self):
        result = projection.forum_topics(
            {
                'total_count': 8,
                'topics': [
                    {
                        'info': {
                            'chat_id': 1,
                            'forum_topic_id': 7,
                            'name': 'Residence',
                            'icon': {'color': 12, 'custom_emoji_id': 0},
                            'creator_id': {
                                '@type': 'messageSenderUser',
                                'user_id': 3,
                            },
                            'is_general': False,
                            'is_closed': False,
                        },
                        'last_message': {
                            'id': 9,
                            'chat_id': 1,
                            'content': {
                                '@type': 'messageText',
                                'text': {'text': 'latest'},
                            },
                        },
                        'order': 10,
                        'is_pinned': True,
                        'unread_count': 2,
                    }
                ],
                'next_offset_date': 11,
                'next_offset_message_id': 12,
                'next_offset_forum_topic_id': 13,
            }
        )

        self.assertEqual(8, result['total_count'])
        self.assertEqual(7, result['topics'][0]['forum_topic_id'])
        self.assertEqual('Residence', result['topics'][0]['name'])
        self.assertEqual('latest', result['topics'][0]['last_message']['text'])
        self.assertEqual(
            {'date': 11, 'message_id': 12, 'forum_topic_id': 13},
            result['next_offset'],
        )

    def test_message_thread_projection_keeps_metadata_and_messages(self):
        result = projection.message_thread(
            {
                'chat_id': 1,
                'message_thread_id': 5,
                'reply_info': {
                    'reply_count': 2,
                    'recent_replier_ids': [
                        {'@type': 'messageSenderUser', 'user_id': 3}
                    ],
                    'last_message_id': 9,
                },
                'unread_message_count': 1,
                'messages': [
                    {
                        'id': 9,
                        'chat_id': 1,
                        'content': {
                            '@type': 'messageText',
                            'text': {'text': 'reply'},
                        },
                    }
                ],
            }
        )

        self.assertEqual(5, result['message_thread_id'])
        self.assertEqual(2, result['reply_info']['reply_count'])
        self.assertEqual('reply', result['messages'][0]['text'])
