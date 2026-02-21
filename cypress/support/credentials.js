export const getAdministratorCredentials = () => ({
	user: Cypress.env("LOGIN_USER") || "Administrator",
	password: Cypress.env("LOGIN_PASSWORD") || "admin",
});
