// Synthetic stand-in for a bw serve configurator: the route registrations
// follow upstream's Koa router style; the handler bodies are placeholders.
export class ExampleServeConfigurator {
  async configureRouter(router: Router) {
    router.get("/status", async (ctx, next) => {
      await next();
    });

    router.get("/list/object/:object", async (ctx, next) => {
      await next();
    });

    router.post(
      "/move/:id/:organizationId",
      async (ctx, next) => {
        await next();
      },
    );

    router.delete('/object/:object/:id', async (ctx, next) => {
      await next();
    });
  }
}
