<script>
    import { userManager } from "$lib/auth/userManager";
  
    const userPromise = userManager.getUser();
  
    userPromise.then(user => {
      if (!user || user.expired) {
        window.location.href = '/invalid-login';
      }
    });
  </script>
  
  <slot />
  