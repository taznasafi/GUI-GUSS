import os
import ast
import warnings
import re
from guss import GUSS
from guss.gussErrors import GussExceptions

class Challenger:
    def __init__(self, **kwargs):
        self.run = kwargs.get('run')
        self.guss_instance = kwargs.get("guss_instance")
        self.as_of_date = kwargs.get("as_of_date")
        self.category = kwargs.get("category")
        self.state_fips_list = kwargs.get("state_fips_list")

    def __repr__(self):
        return self.guss_instance

    def __str__(self):
        return self.guss_instance

    def download(self)->list:

        if self.run:
            guss = self.guss_instance

            if self.category is None:
                raise GussExceptions(f"Please provide category for downloading challenge data")
            else:
                category_params = {
                    'category': self.category
                }

            reference_df = guss.list_challenge_data(as_of_date=self.as_of_date,
                                                    params=category_params,
                                                    file_name=f"challenge_data_as_of_{self.as_of_date}_{self.category}.csv")
            if len(reference_df) ==0:
                raise GussExceptions(f"The Challenge reference table is empty for as of data: {self.as_of_date}")
            num_state = len(self.state_fips_list)
            state_query = ''
            if num_state > 1:

                state_list_query = [f"state_fips == '{x}'" for x in self.state_fips_list]

                if 'all' in [x.lower() for x in self.state_fips_list]:

                    reference_df_filtered = reference_df
                else:
                    state_query = ' or '.join(state_list_query)
                    reference_df_filtered = reference_df.query(f"{state_query}")

            elif num_state == 1:

                if 'all' in [x.lower() for x in self.state_fips_list]:
                    reference_df_filtered = reference_df
                else:

                    state_query = f"state_fips == '{self.state_fips_list[0]}'"
                    reference_df_filtered = reference_df.query(f"{state_query}")
            else:
                raise GussExceptions(message="No state fips list provided")

            if len(reference_df_filtered) == 0:
                raise GussExceptions("check your query params:\n"
                                     f"{reference_df_filtered}\n"
                                     "I got no query back. Try again")
            else:
                print(f"There are about {len(reference_df_filtered)} download files using the following query:{state_query}")

            output_path = []

            for i, row in reference_df_filtered.iterrows():
                print(row)

                file_id = row['file_id']
                file_name = f"{self.category.replace(' ', '_').replace('-', '_')}_{self.as_of_date.replace('-','_')}_{row['state_fips']}_{row['state_name']}.zip"

                saved_output = guss.download_file(data_type='challenge',
                                                  file_id=file_id, file_name=file_name,
                                                  gis_type=None)
                output_path.append(saved_output)

            return output_path
