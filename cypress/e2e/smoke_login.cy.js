describe("Time Tracking smoke test", () => {
	it("shows the login form", () => {
		cy.visit("/login");

		cy.get("#login_email, input[name='login_email']").first().should("be.visible");
		cy.get("#login_password, input[name='login_password']").first().should("be.visible");
		cy.get("button[type='submit']").should("be.visible");
	});
});
