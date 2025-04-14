import sys
import pandas as pd
import numpy as np
import json

def format_output(matrix, coords, reciprocal_info):
    parsed_data = {}

    subsections = matrix.index.to_series().str.split("_").str[0].unique()
    print(subsections)

    for col in matrix.columns:
        # Get reference gene information first
        ref_parts = col.split('_')
        ref_genome = ref_parts[0]
        ref_protein = ref_parts[-1]
        ref_metadata = coords.loc[(coords['genome_name'] == ref_genome) & (coords['protein_name'] == ref_protein)]

        parsed_data[col] = {
            "data": {
                "genome_name": ref_genome,
                "protein_name": ref_protein,
                "direction": ref_metadata['orientation'].values[0] if not ref_metadata.empty else None,
                "rel_position": float(ref_metadata['rel_position'].iloc[0]) if not ref_metadata.empty else None
            }
        }

    for section in subsections:
        if matrix.columns.str.contains(section).any():
            continue
        sub_matrix = matrix[matrix.index.str.startswith(section)]
        print(sub_matrix)

        for col in sub_matrix.columns:
            value_data = []
            for row_index, value in sub_matrix[col].dropna().items():
                print(row_index, value) # ElDoradoDiff_Chr2_02034 95.2
                parts = row_index.split("_")
                genome_name = parts[0]
                protein_name = parts[-1]
                print(genome_name, protein_name)
                metadata = coords.loc[(coords['genome_name'] == parts[0]) & (coords['protein_name'] == parts[-1])]
                print(metadata)

                value_data.append({
                    "genome_name": metadata['genome_name'].values[0],
                    "protein_name": metadata['protein_name'].values[0],
                    "direction": metadata['orientation'].values[0],
                    "score": float(value) if isinstance(value, (int, float, np.number)) else None,
                    "special": None,
                    "rel_position": float(metadata['rel_position'].iloc[0]) if not metadata.empty else None,
                    "is_reciprocal": bool(reciprocal_info.loc[row_index, col])
                })
            
            # Sort value_data by score in descending order
            value_data.sort(key=lambda x: x["score"] if x["score"] is not None else float('-inf'), reverse=True)

            # Store just the first (highest scoring) data object directly
            if value_data:
                parsed_data[col][section] = {
                    "data": value_data
                }
    parsed_data = json.loads(
        json.dumps(parsed_data, default=lambda x: x.tolist() if isinstance(x, (np.ndarray, pd.Series)) else None))
    print(json.dumps(parsed_data, indent=4))






def parse_coordinates(coord_file):
    df = pd.read_excel(coord_file)
    # print(df)

    df['name'] = df['name'].str.replace('^Lsativa_', '', regex=True)
    # print(df)

    df['protein_name'] = df['name'].str.split('_').str[-1]
    df['genome_name'] = df['name'].str.split('_').str[0]
    # print(df)

    df['rel_position'] = df.groupby('genome_name')['position'].rank(method='first')
    # print(df)

    print(df[['name', 'genome_name', 'protein_name', 'position', 'rel_position', 'orientation']])

    return df[['name', 'genome_name', 'protein_name', 'position', 'rel_position', 'orientation']]

def apply_filter(row):
    max_value = row.max()
    return row.where(row >= max_value * 0.95)
    # # Sort values in descending order (ignoring NaNs)
    # sorted_row = row.dropna().sort_values(ascending=False)
    #
    # if len(sorted_row) < 2:
    #     return row  # Return original row if there are less than 2 non-NaN values
    #
    # # Calculate gaps between consecutive values
    # gaps = sorted_row.diff().abs()
    #
    # # Find the index of the largest gap
    # largest_gap_index = gaps.idxmax()
    #
    # # Get the value just before the largest gap
    # threshold = sorted_row.loc[:largest_gap_index].iloc[-1]
    #
    # # Keep only values greater than or equal to the threshold
    # return row.where(row >= threshold, np.nan)





def parse_matrix(matrix_file, coord_file):
    df = pd.read_excel(matrix_file)
    df = df.reset_index(drop=True)
    df = df.set_index(df.columns[0])
    df.index.name = None
    df = df.dropna(how='all')
    df = df.dropna(axis = 1, how='all')

    prefix_dict = {}
    for col in df.columns:
        prefix = col.split('_')[0]
        if prefix not in prefix_dict:
            prefix_dict[prefix] = []
        prefix_dict[prefix].append(col)

    print(df.iloc[0])
    print(prefix_dict)

    print(df.columns[1])

    first_column = df.columns[0]
    filtered = df.filter(like=df.columns[1].split('_')[0])

    # # print(filtered)
    # df_only_cutoffs = filtered[filtered > 55]
    # # print(df_only_cutoffs)
    # #
    # test_result_df = df_only_cutoffs.apply(apply_filter, axis=1)
    # print(test_result_df)

    # only_max_df = filtered.apply(lambda row: row.where(row == row.max(), None), axis = 1)
    # only_max_df = only_max_df[only_max_df > 55]
    # print(only_max_df)

    # # subsections = test_result_df.index.to_series().str.split("_").str[0].unique()
    # # print(subsections)


    df_only_cutoffs = filtered[filtered > 55]
    
    # Get row and column maximums for reciprocal check
    row_maxes = df_only_cutoffs.max(axis=1)
    col_maxes = df_only_cutoffs.max(axis=0)
    
    # Create a DataFrame to store reciprocal information
    reciprocal_info = pd.DataFrame(False, index=df_only_cutoffs.index, columns=df_only_cutoffs.columns)
    
    # Check for reciprocal matches
    for idx in df_only_cutoffs.index:
        for col in df_only_cutoffs.columns:
            value = df_only_cutoffs.loc[idx, col]
            if pd.notna(value):
                is_row_max = value == row_maxes[idx]
                is_col_max = value == col_maxes[col]
                reciprocal_info.loc[idx, col] = is_row_max and is_col_max
    
    test_result_df = df_only_cutoffs.apply(apply_filter, axis=1)
    print(test_result_df)

    coords = parse_coordinates(coord_file)

    output = format_output(test_result_df, coords, reciprocal_info)

    # subsections = test_result_df.index.to_series().str.split("_").str[0].unique()
    # print(subsections)
    #
    # parsed_data = {}
    # for section in subsections:
    #     sub_df = df[df.index.str.startswith(section)]
    #
    # # Extract group names from row indexes (e.g., "GreenTowers", "CobhamGreen")
    # filtered["group"] = filtered.index.str.split("_").str[0]
    #
    # # Function to get max value above cutoff (55)
    # def max_above_cutoff(x):
    #     valid_values = x[x > 55]
    #     return valid_values.max() if not valid_values.empty else np.nan
    #
    # # Group by "group" and find the maximum value for each column
    # result_df = filtered.groupby("group").agg(max_above_cutoff)
    #
    # # Add special rows
    # result_df.loc['Ref=ElDorado'] = np.nan
    # result_df.loc['cutoff=55'] = np.nan
    #
    # # Reset index to make 'group' a column
    # result_df = result_df.reset_index()
    #
    # # Rename 'group' column to 'Group'
    # result_df = result_df.rename(columns={'group': 'Group'})
    #
    # print("\nResult (maximum value per group and column):")
    # print(result_df)



# Usage

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python matrix_parse.py <matrix_file.xlsx> <coordinate_file.xlsx>")
        sys.exit(1)

    matrix_file = sys.argv[1]
    coord_file = sys.argv[2]

    parse_matrix(matrix_file, coord_file)