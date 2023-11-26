# coding=utf-8
# Copyright 2018-2023 EvaDB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import numpy as np
import pandas as pd

import aiohttp
import asyncio
import nest_asyncio
nest_asyncio.apply()
import backoff

import json
import time
import requests

from evadb.catalog.catalog_type import NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe


class BingSearchFn(AbstractFunction):
    @property
    def name(self) -> str:
        return "bing_search_fn"

    @setup(batchable=True, cacheable=True)
    def setup(self):
        # self.subscription_key = 'e1e7a319fe644fa3920218b7b5067e33'
        # self.search_url = "https://api.bing.microsoft.com/v7.0/search"
        self.subscription_key = 'cc84a64c7e8643129963a110dfa9543a'
        self.search_url = "https://api.bing.microsoft.com/v7.0/search"

    @staticmethod
    async def fetch(session, search_url, headers, params):
        async with session.get(search_url, headers=headers, params=params) as response:
            return await response.json()

    async def search_links(self, session, search_term):
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
        params = {"q": search_term}
        try:
            response_json = await self.fetch(session, self.search_url, headers, params)
            links = []
            if 'webPages' in response_json:
                web_pages = response_json['webPages']['value']
                for page in web_pages:
                    links.append(page['url'])
            return links[:6]
        except Exception as e:
            print(f"Error in Bing search for {search_term}: {e}")
            return []

    async def search_all(self, search_terms):
        async with aiohttp.ClientSession() as session:
            tasks = [self.search_links(session, term) for term in search_terms]
            return await asyncio.gather(*tasks)

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["search_term"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["links"],
                column_types=[NdArrayType.STR],
                column_shapes=[(5)],
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        search_terms = df[df.columns[0]].tolist()
        loop = asyncio.get_event_loop()
        links_list = loop.run_until_complete(self.search_all(search_terms))
        ret = pd.DataFrame()
        ret["links"] = links_list
        return ret