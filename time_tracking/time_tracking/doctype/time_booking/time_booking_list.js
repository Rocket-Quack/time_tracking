function rebuildTimeBookingActionsMenu(listview) {
	const exportLabel = __("Export", null, "Button in list view actions menu");
	listview.actions_menu_items = (listview.actions_menu_items || []).filter(
		(item) => item.label !== exportLabel
	);

	listview.page.clear_actions_menu();

	const actions = (listview.actions_menu_items || []).concat(
		listview.workflow_action_menu_items || []
	);
	actions.forEach((item) => {
		const $item = listview.page.add_actions_menu_item(item.label, item.action, item.standard);
		if (item.class) {
			$item.addClass(item.class);
		}
		if (item.is_workflow_action && $item) {
			listview.workflow_action_items = listview.workflow_action_items || {};
			listview.workflow_action_items[item.name] = $item;
		}
	});
}

frappe.listview_settings["Time Booking"] = {
	onload(listview) {
		if (frappe.model.can_export("Time Booking")) {
			return;
		}

		rebuildTimeBookingActionsMenu(listview);
	},
};
