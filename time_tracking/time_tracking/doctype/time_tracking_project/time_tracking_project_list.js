frappe.listview_settings["Time Tracking Project"] = {
	add_fields: ["project_status", "not_bookable", "project_name"],
	onload(listview) {
		if (listview && listview.meta) {
			listview.meta.title_field = "project_name";
			listview.meta.show_title_field_in_link = 1;
		}
		const filterArea = () => listview && listview.filter_area;

		const removeFieldFilters = (fieldname) => {
			const area = filterArea();
			if (!area || !area.filters) {
				return;
			}
			const filters = area.filters.slice();
			filters.forEach((filter) => {
				const filterField = filter.fieldname || (filter.df && filter.df.fieldname) || "";
				if (filterField === fieldname) {
					if (area.remove_filter) {
						area.remove_filter(filter);
					} else if (filter.remove) {
						filter.remove();
					}
				}
			});
		};

		const removeInvalidParentFilters = () => {
			const area = filterArea();
			if (!area || !area.filters) {
				return false;
			}

			let changed = false;
			const filters = area.filters.slice();
			filters.forEach((filter) => {
				const filterField = filter.fieldname || (filter.df && filter.df.fieldname) || "";
				const rawValue =
					filter.value !== undefined
						? filter.value
						: filter.get_value
							? filter.get_value()
							: filter[3];
				if (filterField !== "parent_time_tracking_project") {
					return;
				}
				if (rawValue !== "" && rawValue !== null && rawValue !== "Time Tracking Project") {
					return;
				}
				changed = true;
				if (area.remove_filter) {
					area.remove_filter(filter);
				} else if (filter.remove) {
					filter.remove();
				}
			});

			return changed;
		};

		const addFilter = (fieldname, value) => {
			const area = filterArea();
			if (!area) {
				return;
			}
			if (area.add_filter) {
				area.add_filter(listview.doctype, fieldname, "=", value);
				return;
			}
			if (area.add) {
				area.add([listview.doctype, fieldname, "=", value]);
			}
		};

		const applyFilter = (fieldname, value) => {
			removeFieldFilters(fieldname);
			addFilter(fieldname, value);
			listview.refresh();
		};

		const clearFilters = () => {
			const area = filterArea();
			if (area && area.clear_filters) {
				area.clear_filters();
			}
			listview.refresh();
		};

		listview.page.add_inner_button(__("Active"), () => {
			applyFilter("project_status", "Active");
		});
		listview.page.add_inner_button(__("Inactive"), () => {
			applyFilter("project_status", "Inactive");
		});
		listview.page.add_inner_button(__("Bookable"), () => {
			applyFilter("not_bookable", 0);
		});
		listview.page.add_inner_button(__("Not Bookable"), () => {
			applyFilter("not_bookable", 1);
		});
		listview.page.add_inner_button(__("Clear Filters"), clearFilters);

		if (removeInvalidParentFilters()) {
			listview.refresh();
		}
	},
	get_indicator(doc) {
		const status = (doc.project_status || "Active").trim();
		if (status === "Inactive") {
			return [__("Inactive"), "red", "project_status,=,Inactive"];
		}
		return [__("Active"), "green", "project_status,=,Active"];
	},
	formatters: {
		name(value, df, doc) {
			return doc.project_name || value;
		},
		project_status(value, df, doc) {
			const status = (doc.project_status || "Active").trim();
			const color = status === "Inactive" ? "red" : "green";
			return `<span class="indicator ${color}">${__(status)}</span>`;
		},
		not_bookable(value, df, doc) {
			const isNotBookable = Number(doc.not_bookable) === 1;
			const label = isNotBookable ? __("Not Bookable") : __("Bookable");
			const color = isNotBookable ? "red" : "green";
			return `<span class="indicator ${color}">${label}</span>`;
		},
	},
};
