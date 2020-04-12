#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_commons.constants import START_PENDING_EVAL_NOTE, CONFIG_CRYPTO_CURRENCY, CONFIG_CRYPTO_CURRENCIES
from octobot_commons.tentacles_management.advanced_manager import get_single_deepest_child_class
from octobot_evaluators.evaluator.social_evaluator import SocialEvaluator
from octobot_services.constants import FEED_METADATA
from tentacles.Services.Services_feeds import RedditServiceFeed
from tentacles.Evaluator.Util.text_analysis import TextAnalysis
from tentacles.Evaluator.Util.overall_state_analysis import OverallStateAnalyser

CONFIG_REDDIT = "reddit"
CONFIG_REDDIT_SUBREDDITS = "subreddits"
CONFIG_REDDIT_ENTRY = "entry"
CONFIG_REDDIT_ENTRY_WEIGHT = "entry_weight"


# RedditForumEvaluator is used to get an overall state of a market, it will not trigger a trade
# (notify its evaluators) but is used to measure hype and trend of a market.
class RedditForumEvaluator(SocialEvaluator):

    SERVICE_FEED_CLASS = RedditServiceFeed

    def __init__(self):
        SocialEvaluator.__init__(self)
        self.overall_state_analyser = OverallStateAnalyser()
        self.count = 0
        self.sentiment_analyser = None
        self.is_self_refreshing = True

    @classmethod
    def get_is_cryptocurrencies_wildcard(cls) -> bool:
        """
        :return: True if the evaluator is not cryptocurrency dependant else False
        """
        return False

    def _print_entry(self, entry_text, entry_note, count=""):
        self.logger.debug(f"New reddit entry ! : {entry_note} | {count} : {self.cryptocurrency} : Link : {entry_text}")

    async def _feed_callback(self, data):
        if self._is_interested_by_this_notification(data[FEED_METADATA]):
            self.count += 1
            entry_note = self._get_sentiment(data[CONFIG_REDDIT_ENTRY])
            if entry_note != START_PENDING_EVAL_NOTE:
                self.overall_state_analyser.add_evaluation(entry_note, data[CONFIG_REDDIT_ENTRY_WEIGHT], False)
                if data[CONFIG_REDDIT_ENTRY_WEIGHT] > 3:
                    link = f"https://www.reddit.com{data[CONFIG_REDDIT_ENTRY].permalink}"
                    self._print_entry(link, entry_note, str(self.count))
            self.eval_note = self.overall_state_analyser.get_overall_state_after_refresh()
            await self.evaluation_completed(self.cryptocurrency)

    def _get_sentiment(self, entry):
        # analysis entry text and gives overall sentiment
        reddit_entry_min_length = 50
        # ignore usless (very short) entries
        if entry.selftext and len(entry.selftext) >= reddit_entry_min_length:
            return -1 * self.sentiment_analyser.analyse(entry.selftext)
        return START_PENDING_EVAL_NOTE

    def _is_interested_by_this_notification(self, notification_description):
        # true if the given subreddit is in this cryptocurrency's subreddits configuration
        if self.specific_config[CONFIG_REDDIT_SUBREDDITS]:
            for subreddit in self.specific_config[CONFIG_REDDIT_SUBREDDITS][self.cryptocurrency]:
                if subreddit.lower() == notification_description:
                    return True
        return False

    def _get_config_elements(self, key):
        if CONFIG_CRYPTO_CURRENCIES in self.specific_config and self.specific_config[CONFIG_CRYPTO_CURRENCIES]:
            return {cc[CONFIG_CRYPTO_CURRENCY]: cc[key] for cc in self.specific_config[CONFIG_CRYPTO_CURRENCIES]
                    if cc[CONFIG_CRYPTO_CURRENCY] == self.cryptocurrency}
        return {}

    def _format_config(self):
        # remove other symbols data to avoid unnecessary entries
        self.specific_config[CONFIG_REDDIT_SUBREDDITS] = self._get_config_elements(CONFIG_REDDIT_SUBREDDITS)

    async def prepare(self):
        self._format_config()
        self.sentiment_analyser = get_single_deepest_child_class(TextAnalysis)()
