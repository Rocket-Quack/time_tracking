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
		cy.get("#login_email, input[name='login_email']")
			.first()
			.clear()
			.type(user, { log: false });
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

		const workspacePathPattern =
			/^\/(desk\/time-tracking|app\/time-tracking|app\/workspace\/time-tracking)(\/.*)?$/;

		cy.location("pathname", { timeout: 15000 }).then((pathname) => {
			if (!workspacePathPattern.test(pathname)) {
				cy.get(
					'#page-desktop img[alt="Time Tracking"], #page-desktop [data-original-title="Time Tracking"], #page-desktop [data-id="Time Tracking"]',
					{ timeout: 15000 }
				)
					.first()
					.should("be.visible")
					.scrollIntoView()
					.click({ force: true });
			}
		});

		cy.location("pathname", { timeout: 15000 }).then((pathname) => {
			if (!workspacePathPattern.test(pathname)) {
				cy.get('[data-id="Time Tracking"] > .icon-caption > .icon-title', {
					timeout: 15000,
				})
					.first()
					.should("be.visible")
					.click({ force: true });
			}
		});
		cy.location("pathname", { timeout: 15000 }).should((pathname) => {
			expect(pathname).to.match(workspacePathPattern);
		});
		cy.contains("body", "Time Tracking", { timeout: 15000 });

		cy.contains('div[item-name="Weekly Booking"] span.sidebar-item-label', "Weekly Booking", {
			timeout: 15000,
		}).should("be.visible");

		cy.contains('div[item-name="Time Booking"] span.sidebar-item-label', "Time Booking", {
			timeout: 15000,
		}).should("be.visible");

		cy.contains(
			'div[item-name="My Project Access"] span.sidebar-item-label',
			"My Project Access",
			{ timeout: 15000 }
		).should("be.visible");

		cy.get('[item-name="Time Tracking Settings"] > .standard-sidebar-item').should(
			"be.visible"
		);
	});
});
