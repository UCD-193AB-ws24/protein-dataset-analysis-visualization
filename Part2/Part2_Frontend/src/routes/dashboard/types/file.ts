	export interface File {
		file_name: string;
		file_type: string;
	}

	export interface FileGroup {
		id: string;
		title: string;
		description: string;
		genomes: string[];
		num_genes: number;
		num_domains: number;
		is_domain_specific: boolean;
		files: File[];
		created_at: string;
		last_updated_at: string;
	}