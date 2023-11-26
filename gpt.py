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

import dotenv
dotenv.load_dotenv('/home/oscar/dbi/hfsm/.env')
from openai import AsyncOpenAI
client = AsyncOpenAI()


import json
import time
import requests

from evadb.catalog.catalog_type import NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe


class GPTSearchFn(AbstractFunction):
    @property
    def name(self) -> str:
        return "gpt_search_fn"

    @setup(batchable=True, cacheable=True)
    def setup(self):
        pass

    async def search_links(self, session, search_term):
        try:
            completion = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=90,
                messages=[{"role": "system", "content": f"Search: {search_term}"}],
                temperature=0.5,
                timeout=15,
                )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Error in GPT search for {search_term}: {e}")
            return ''

    async def search_all(self, search_terms):
        async with aiohttp.ClientSession() as session:
            tasks = [self.search_links(session, term) for term in search_terms]
            return await asyncio.gather(*tasks)

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["query"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["reply"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        search_terms = df[df.columns[0]].tolist()
        loop = asyncio.get_event_loop()
        answers_list = loop.run_until_complete(self.search_all(search_terms))
        ret = pd.DataFrame()
        ret["reply"] = answers_list
        return ret