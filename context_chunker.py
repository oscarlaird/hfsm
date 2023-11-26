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

from evadb.catalog.catalog_type import NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe


class DummyFn(AbstractFunction):
    @property
    def name(self) -> str:
        return "chunk_text"

    # TODO: extract text, email, or img srcs from html
    @setup(batchable=True, cacheable=True)
    def setup(self):
        pass

    def chunk_text(self, text, chunk_size=140, max_chunks=60):
        words = text.split()
        # filter out words which are longer than 30 characters
        words = [word for word in words if len(word) < 30]
        chunks = []
        current_chunk = ''

        for word in words:
            if len(current_chunk) + len(word) + 1 > chunk_size:
                chunks.append(current_chunk)
                current_chunk = word
            else:
                current_chunk += ' ' + word if current_chunk else word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks[:max_chunks]

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["text"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["chunks"],
                column_types=[NdArrayType.STR],
                column_shapes=[(5)],
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        # get all the urls as a list
        texts = df[df.columns[0]].tolist()
        chunks = [ self.chunk_text(text) for text in texts ]
        ret = pd.DataFrame()
        ret["chunks"] = chunks
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