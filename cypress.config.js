const { defineConfig } = require("cypress");

module.exports = defineConfig({
	viewportWidth: 1920,
	viewportHeight: 1080,
	e2e: {
		baseUrl: process.env.CYPRESS_BASE_URL || "http://dev16.localhost:8000",
		specPattern: "cypress/e2e/**/*.cy.js",
		supportFile: "cypress/support/e2e.js",
	},
	projectId: process.env.CYPRESS_PROJECT_ID,
	screenshotOnRunFailure: true,
	video: true,
});
