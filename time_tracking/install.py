def after_install():
	from time_tracking.role_hierarchy import backfill_time_tracking_role_hierarchy

	backfill_time_tracking_role_hierarchy()


def after_migrate():
	from time_tracking.role_hierarchy import backfill_time_tracking_role_hierarchy

	backfill_time_tracking_role_hierarchy()
