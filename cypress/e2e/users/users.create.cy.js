describe("Users - create time tracking user", () => {
	const email = "admin@local.dev";
	const firstName = "Time Tracking Admin";

	before(() => {
		cy.loginByApiSession();
		cy.deleteUserByEmail(email);
	});

	after(() => {
		cy.loginByApiSession();
		cy.deleteUserByEmail(email);
	});

	it("creates a time tracking admin user via full form", () => {
		cy.loginByApiSession();
		cy.visit("/desk/user");

		cy.contains("button, a", "Add User").should("be.visible").click();
		cy.contains("button, a", "Edit Full Form").should("be.visible").click();
		cy.url().should("include", "/desk/user/new-user-");

		// Close quick-entry modal if it is still visible over full form.
		cy.get("body").then(($body) => {
			if ($body.find(".modal.show:visible").length) {
				cy.get(".modal.show:visible .btn-modal-close").first().click({ force: true });
			}
		});

		cy.get(".modal.show:visible", { timeout: 10000 }).should("not.exist");
		cy.get(".modal-backdrop", { timeout: 10000 }).should("not.exist");

		cy.get('[data-fieldname="email"] input').first().should("be.visible").clear().type(email);
		cy.get('[data-fieldname="first_name"] input')
			.first()
			.should("be.visible")
			.clear()
			.type(firstName);

		cy.get("#page-User .primary-action").first().click();

		// "No Roles Specified" dialog can appear on first save. Close it if present.
		cy.get("body").then(($body) => {
			const $noRolesModal = $body
				.find(".modal.show:visible")
				.filter((_, el) => Cypress.$(el).text().includes("No Roles Specified"));

			if ($noRolesModal.length) {
				cy.wrap($noRolesModal.first())
					.find(".btn-modal-close, .btn-primary")
					.first()
					.click({ force: true });
			}
		});

		cy.visit("/desk/user");

		cy.contains("#page-List\\/User\\/List a, #page-List\\/User\\/List .list-row-container", firstName)
			.should("be.visible");
		cy.contains("#page-List\\/User\\/List a, #page-List\\/User\\/List .list-row-container", email)
			.should("be.visible");
	});
});
