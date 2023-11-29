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
from openai import OpenAI
client = OpenAI()


import json
import time
import requests

from evadb.catalog.catalog_type import NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe

import hashlib
import base64

def hash_prompt_for_filename(prompt):
    # Convert the prompt to bytes
    prompt_bytes = prompt.encode()
    # Create a SHA-256 hash object
    sha256 = hashlib.sha256()
    # Update the hash object with the bytes of the prompt
    sha256.update(prompt_bytes)
    # Get the hash in bytes
    hash_bytes = sha256.digest()
    # Encode the hash bytes using base64
    b64_encoded = base64.b64encode(hash_bytes)
    # Decode the base64 bytes into a string and truncate to 6 characters
    filename = b64_encoded.decode()[:6]
    return filename

class GPTSearchFn(AbstractFunction):
    @property
    def name(self) -> str:
        return "gpt_search_fn"

    @setup(batchable=True, cacheable=True)
    def setup(self):
        pass

    def search_links(self, search_term):
        # sleep for 12s
        print('sleeping 12s')
        time.sleep(12)
        try:
            # abridge search term to 1000 characters
            search_term = search_term[:1000]

            img_response = client.images.generate(
                model="dall-e-3",
                prompt=search_term,
                n=1,
                size="1024x1024"
            )
            url = img_response.data[0].url
            fname = hash_prompt_for_filename(search_term) + '.png'
            # save the image at url to ./dalle_images/{fname}.png
            img_data = requests.get(url).content
            with open(f"./dalle_images/{fname}", 'wb') as handler:
                handler.write(img_data)

            # completion = await client.chat.completions.create(
                # model="gpt-3.5-turbo",
                # max_tokens=90,
                # messages=[{"role": "system", "content": f"Search: {search_term}"}],
                # temperature=0.5,
                # )
            return img_response.data[0].url
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
                columns=["img_url"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        search_terms = df[df.columns[0]].tolist()
        # loop = asyncio.get_event_loop()
        # answers_list = loop.run_until_complete(self.search_all(search_terms))
        answers_list = [self.search_links(term) for term in search_terms]
        ret = pd.DataFrame()
        ret["img_url"] = answers_list
        return ret