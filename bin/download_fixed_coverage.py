import os
import ast
import warnings
import re
import pandas as pd
import geopandas as gpd
from guss import GUSS
from guss.gussErrors import GussExceptions
from guss.GUSS import GPK_OUTPUT, SHP_OUTPUT


class FixedCoverageDealer:
    def __init__(self, **kwargs):
        self.run = kwargs.get('run')
        self.guss_instance = kwargs.get("guss_instance")
        self.as_of_date = kwargs.get("as_of_date")
        self.data_type = kwargs.get("data_type")
        self.provider_id_list = kwargs.get("provider_id_list")
        self.state_fips_list = kwargs.get("state_fips_list")
        self.technology_list = kwargs.get("technology_list")
        self.technology_type = kwargs.get("technology_type")
        self.polygonize = kwargs.get("polygonize")
        self.gis_type = kwargs.get("gis_type")

    def __repr__(self):
        return self.guss_instance
    def __str__(self):
        return self.guss_instance

    def download(self) -> list:

        if self.data_type == 'availability':
            pass
        else:
            raise GussExceptions(message="Please make sure that the data_type should be:\n"
                                         "\t 1) availability (default value)")

        if self.run:

            guss = self.guss_instance

            category = 'Provider'
            subcategory = guss.category_subcategory[category][1]
            technology_type = guss.technology_type[1]

            reference_df = guss.get_download_reference(as_of_date=self.as_of_date)

            if reference_df.empty:
                raise GussExceptions(message="please check your as of date, no reference found")

            reference_df_filtered = reference_df[

                (reference_df['category'] == f'{category}')
                & (reference_df['subcategory'] == f"{subcategory}")
                & (reference_df['technology_type'] == f"{technology_type}")
                & (reference_df["file_type"] == 'csv')

                ]
            if reference_df_filtered.empty:
                raise GussExceptions(
                    message="No reference after filtering. Check your category or subcategory or technology_type,"
                            " or file_type query parameters")

            num_state = len(self.state_fips_list)
            num_technology = len(self.technology_list)
            num_provider = len(self.provider_id_list)

            if num_state > 1:
                state_list_query = [f"state_fips == '{x}'" for x in self.state_fips_list]
                state_query = ' or '.join(state_list_query)
                filter_df = reference_df_filtered.query(f"{state_query}")
            elif num_state == 1:
                if 'all' in [x.lower() for x in self.state_fips_list]:
                    filter_df = reference_df_filtered
                else:
                    state_query = f"state_fips == '{self.state_fips_list[0]}'"
                    filter_df = reference_df_filtered.query(f"{state_query}")
            else:
                raise GussExceptions(message="No state fips list provided")

            if num_technology > 1:

                technology_list = [f"{x}" for x in self.technology_list]

                if 'all' in [str(x).lower() for x in technology_list]:
                    raise GussExceptions(message="check technology code list, 'all' should not be provided with other code "
                                                 "techs")

                technology_query = "|".join(technology_list)

                technology_query = fr"\b(?:{technology_query})\b"

                filter_df = filter_df[
                    filter_df['technology_code'].str.contains(technology_query, flags=re.IGNORECASE, regex=True)]

            elif num_technology == 1:
                if 'all' in [str(x).lower() for x in self.technology_list]:
                    filter_df = reference_df_filtered
                else:
                    technology_query = f"{self.technology_list[0]}"
                    filter_df = filter_df[filter_df['technology_code'].str.contains(technology_query)]
            else:
                raise GussExceptions(message="No technology id list provided")

            if num_provider > 1:
                provider_id_list_query = [f"provider_id == '{x}'" for x in self.provider_id_list]
                provider_id_query = ' or '.join(provider_id_list_query)
                filter_df = filter_df.query(provider_id_query)

            elif num_provider == 1:
                if 'all' in self.provider_id_list:
                    filter_df = filter_df
                else:
                    provider_id_query = f"provider_id == '{self.provider_id_list[0]}'"
                    filter_df = filter_df.query(provider_id_query)
            else:
                raise GussExceptions(message="No provider id list provided")

            filter_df = filter_df.sort_values(
                by=['provider_id', 'state_fips', "technology_code", 'speed_tier'])

            print(f"There are total of {len(filter_df)} number of files ready for download.")

            output_path_list = []
            for i, row in filter_df.iterrows():
                file_id = row['file_id']
                file_name = f"{technology_type.replace(' ', '')}_{subcategory.replace(' ', '')}_{row['file_name']}.zip"

                if guss.stop:
                    print("Stopped download per User request")
                    guss.stop = True
                    break
                else:

                    saved_output = guss.download_file(data_type=self.data_type, file_id=file_id, file_name=file_name, gis_type=None)

                    if self.polygonize:
                        df = pd.read_csv(saved_output, compression='zip')
                        df['geometry'] = df['h3_res8_id'].apply(guss.polygonize)

                        gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=4326)
                        if self.gis_type == 'gpkg':
                            output_path = os.path.join(GPK_OUTPUT, file_name.replace('.zip', '.gpkg'))
                            layer_name = file_name.replace('.zip', '.gpkg')
                            gdf.to_file(output_path, layer=layer_name)
                            print(f"GeoPackage saved to {output_path}")

                        elif self.gis_type == 'shp':
                            output_path = os.path.join(SHP_OUTPUT, file_name.replace('.zip', '.shp'))
                            gdf.to_file(output_path)
                            print(f"shp saved to {output_path}")
                        else:
                            raise GussExceptions(message="Oh no, gis_type was not provided, please indicate gis_type = 'shp' "
                                                         "or 'gpkg'")

                    output_path_list.append(saved_output)
