import threading

# Whether the image index needs updating on the server servicing thread
index_needs_updating = False
# Whether the image index is going through rebuilding on the command line thread
rebuild_in_progress = False

# Shared lock to maintain access around the image index
lock = threading.Lock()
# Newest ImageMatcher image index ready to be copied when index_needs_updating==True and rebuild_in_progress==False
matcher_index = None
