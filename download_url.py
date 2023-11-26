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

from evadb.catalog.catalog_type import NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe

class DummyFn(AbstractFunction):
    @property
    def name(self) -> str:
        return "dummy_fn"

    @setup(batchable=True, cacheable=True)
    def setup(self):
        pass


    @staticmethod
    async def fetch(session, url):
        async with session.get(url) as response:
            return await response.text()
    @backoff.on_exception(backoff.expo,
                        aiohttp.ClientError,
                        max_tries=8)
    async def download_url(self, session, url):
        try:
            html = await self.fetch(session, url)
            return html
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return ''
    async def download_all(self, urls):
        async with aiohttp.ClientSession() as session:
            tasks = [self.download_url(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["url"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["html"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        # get all the urls as a list
        urls = df[df.columns[0]].tolist()
        loop = asyncio.get_event_loop()
        # htmls = asyncio.run(self.download_all(urls))
        htmls = loop.run_until_complete(self.download_all(urls))
        # return as a dataframe
        ret = pd.DataFrame()
        ret["html"] = htmls
        return ret



"""
    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["data"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["features"],
                column_types=[NdArrayType.FLOAT32],
                column_shapes=[(1, 384)],
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        def _forward(row: pd.Series) -> np.ndarray:
            data = row
            embedded_list = self.model.encode(data)
            return embedded_list

        ret = pd.DataFrame()
        ret["features"] = df.apply(_forward, axis=1)
        return ret

"""