<script lang="ts">
    import { signUp } from '$lib/auth/auth';
    import { goto } from '$app/navigation';
  
    let email = '';
    let password = '';
    let error = '';
    let success = '';
  
    async function handleSignup() {
      try {
        await signUp(email, password);
        success = 'Signup successful! Check your email for the verification code.';
        goto(`/verify?email=${encodeURIComponent(email)}`);
      } catch (err: any) {
        error = err.message || 'Signup failed.';
      }
    }
  </script>
  
  <h1>Sign Up</h1>
  <input bind:value={email} placeholder="Email" />
  <input type="password" bind:value={password} placeholder="Password" />
  <button on:click={handleSignup}>Sign Up</button>
  
  {#if error}
    <p style="color: red">{error}</p>
  {/if}
  {#if success}
    <p style="color: green">{success}</p>
  {/if}
  