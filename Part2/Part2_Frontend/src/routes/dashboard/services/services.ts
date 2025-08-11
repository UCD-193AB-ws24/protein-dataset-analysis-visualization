import { API_BASE_URL } from '$lib/envs';
import type { FileGroup } from '../types/file';

export async function fetchUserFileGroups(access_token: string, id_token: string) {
  const response = await fetch(`${API_BASE_URL}/get_user_file_groups`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token}`,
      'X-ID-Token': id_token
    }
  });

  if (!response.ok) {
    throw new Error(`Error fetching projects: ${response.status} ${response.statusText}`);
  }

  // Assuming API returns: { file_groups: FileGroup[] }
  return response.json() as Promise<{ file_groups: FileGroup[] }>;
}

export async function deleteGroup(groupId: string, access_token: string) {
  const response = await fetch(
    `${API_BASE_URL}/delete_group?groupId=${encodeURIComponent(groupId)}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${access_token}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Error deleting group: ${response.status} ${response.statusText}`);
  }

  return true;
}
