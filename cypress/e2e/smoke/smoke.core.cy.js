import { getAdministratorCredentials } from "../../support/credentials";

describe("Smoke: Core Application", () => {
	it("shows login form controls", () => {
		cy.visit("/login");

		cy.get("#login_email, input[name='login_email']").first().should("be.visible");
		cy.get("#login_password, input[name='login_password']").first().should("be.visible");
		cy.get("button[type='submit']").should("be.visible");
	});

	it("logs in through the UI", () => {
		const { user, password } = getAdministratorCredentials();

		cy.visit("/login");
		cy.get("#login_email, input[name='login_email']").first().clear().type(user, { log: false });
		cy.get("#login_password, input[name='login_password']").first().clear().type(password, {
			log: false,
		});
		cy.get("#page-login button.btn-login, button[type='submit']").first().click();
		cy.url().should("include", "/desk");
	});

	it("opens desk with an authenticated API session", () => {
		cy.loginByApiSession();
		cy.visit("/app");
		cy.getCookie("sid").should("exist");
		cy.get('#page-desktop img[alt="Time Tracking"]').should(
			"have.attr",
			"src",
			"/assets/time_tracking/images/time-tracking-logo.png"
		);
		cy.get('#page-desktop div[data-original-title="Time Tracking"]').should(
			"have.text",
			"Time Tracking"
		);
	});

	it("opens Time Tracking workspace from desktop", () => {
		cy.loginByApiSession();
		cy.visit("/app");

		cy.get('#page-desktop img[alt="Time Tracking"]').click();
		cy.get("#editorjs span.h1").should("be.visible").and("have.text", "Time Tracking");
		cy.get("#editorjs div.text-muted").should(
			"have.text",
			"Log hours, plan weeks, and track targets"
		);

		cy.get('div[item-name="Weekly Booking"] span.sidebar-item-label').should("be.visible");
		cy.get('div[item-name="Time Booking"] span.sidebar-item-label').should("be.visible");
		cy.get('div[item-name="My Project Access"] span.sidebar-item-label').should("be.visible");
	});
});
