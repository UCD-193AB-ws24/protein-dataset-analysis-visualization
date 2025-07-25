import pandas as pd

def process_domain_field(df):
    try:
        domain_columns = [col for col in df.columns if 'domain' in col]
        if len(domain_columns) == 0:
            raise ValueError("No domain columns found (should be in format 'domainX_NAME_start/end/NA)")

        domain_names = set()
        domain_col_names = set()
        for col in domain_columns:
            domain_col_names.add(col)
            parts = col.split('_')
            if len(parts) < 2:
                raise ValueError(f"Invalid domain format, needs underscore: {col}")

            if len(parts) == 3:
                domain_name = '_'.join(parts[1:-1]) # Also handles cases where domain names have underscores
            elif len(parts) == 2:
                domain_name = parts[-1]
            domain_names.add(domain_name)

        # Group columns by domain name
        domain_cols = {}
        for domain in domain_names:
            domain_cols[domain] = [col for col in domain_columns if domain in col]

        # Validate each domain's columns
        for domain, cols in domain_cols.items():
            has_start = any(col.endswith('_start') for col in cols)
            has_end = any(col.endswith('_end') for col in cols)

            # If domain has start/end positions, they must be in the same file
            if has_start or has_end:
                if not (has_start and has_end):
                    raise ValueError(f"Domain {domain} must have both start and end positions in the same file")

        return list(domain_names), list(domain_col_names)
    except Exception as e:
        raise ValueError(f"Error processing domain field: {str(e)}") 