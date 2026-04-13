describe("Time Tracking Settings - Holidays", () => {
	const currentYear = new Date().getFullYear();
	const expectedName = `${currentYear}-Holiday-List`;

	function deleteCurrentYearHolidayList() {
		return cy.request({
			method: "POST",
			url: "/api/method/frappe.client.delete",
			body: {
				doctype: "Time Tracking Holiday List",
				name: expectedName,
			},
			failOnStatusCode: false,
		});
	}

	function setHolidaySetting(value) {
		return cy.request({
			method: "POST",
			url: "/api/method/frappe.client.set_value",
			body: {
				doctype: "Time Tracking Settings",
				name: "Time Tracking Settings",
				fieldname: "enable_holiday_list",
				value,
			},
			failOnStatusCode: false,
		});
	}

	function createCurrentYearHolidayList() {
		return cy.request({
			method: "POST",
			url: "/api/method/frappe.client.insert",
			body: {
				doc: {
					doctype: "Time Tracking Holiday List",
					year: String(currentYear),
					holidays: [],
				},
			},
		});
	}

	beforeEach(() => {
		cy.loginByApiSession();
		deleteCurrentYearHolidayList();
		setHolidaySetting(0);
	});

	afterEach(() => {
		cy.loginByApiSession();
		setHolidaySetting(0);
		deleteCurrentYearHolidayList();
	});

	it("shows a blocking popup and opens the current year holiday list creation flow", () => {
		cy.visit("/desk/time-tracking-settings/Time Tracking Settings");

		cy.get('[data-fieldname="enable_holiday_list"] input[type="checkbox"]').check({
			force: true,
		});

		cy.contains(".modal-title", "Holiday List Required").should("be.visible");
		cy.contains(".modal-body, .frappe-control", expectedName).should("be.visible");
		cy.contains(
			".modal-footer .btn-primary, .modal-footer .btn",
			"Create Holiday List"
		).click();

		cy.url().should("include", "/time-tracking-holiday-list/new-");
		cy.get('[data-fieldname="year"] input, [data-fieldname="year"] select')
			.first()
			.should("have.value", String(currentYear));
	});

	it("keeps holidays enabled when the current year holiday list exists", () => {
		createCurrentYearHolidayList();

		cy.visit("/desk/time-tracking-settings/Time Tracking Settings");
		cy.get('[data-fieldname="enable_holiday_list"] input[type="checkbox"]').check({
			force: true,
		});

		cy.contains(".modal-title", "Holiday List Required").should("not.exist");
		cy.get('[data-fieldname="enable_holiday_list"] input[type="checkbox"]').should(
			"be.checked"
		);
	});
});
