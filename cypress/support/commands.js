import { getAdministratorCredentials } from "./credentials";

Cypress.Commands.add("loginByApiSession", () => {
	const { user, password } = getAdministratorCredentials();

	cy.request({
		method: "POST",
		url: "/api/method/login",
		form: true,
		body: {
			usr: user,
			pwd: password,
		},
	}).then((resp) => {
		expect(resp.status).to.eq(200);
	});
});

Cypress.Commands.add("deleteUserByEmail", (email) => {
	return cy
		.request({
			method: "POST",
			url: "/api/method/frappe.client.delete",
			body: {
				doctype: "User",
				name: email,
			},
			failOnStatusCode: false,
		})
		.then((resp) => {
			expect([200, 404, 417]).to.include(resp.status);
		});
});
