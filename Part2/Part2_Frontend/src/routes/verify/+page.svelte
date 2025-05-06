<script lang="ts">
    import { page } from '$app/stores';
    import { confirmSignUp } from '$lib/auth/auth';
    import { goto } from '$app/navigation';
  
    let code = '';
    let error = '';
    let success = '';
    let email = '';
  
    $: email = $page.url.searchParams.get('email') ?? '';
  
    async function handleVerify() {
      try {
        await confirmSignUp(email, code);
        success = 'Email verified! You can now log in.';
        goto('/welcome');
      } catch (err: any) {
        error = err.message || 'Verification failed.';
      }
    }
  </script>
  
  <h1>Verify Your Email</h1>
  <p>Enter the verification code sent to {email}:</p>
  <input bind:value={code} placeholder="Verification code" />
  <button on:click={handleVerify}>Verify</button>
  
  {#if error}
    <p style="color: red">{error}</p>
  {/if}
  {#if success}
    <p style="color: green">{success}</p>
  {/if}
  