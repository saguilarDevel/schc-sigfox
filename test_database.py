from database import Database
import config.config as config


# Init database with the bucket name
Database.initialize(config.BUCKET_NAME)

# Save some example to the database
Database.save(config.BUCKET_NAME, "some example text", 'test-database')

# Read from database
example = Database.read(config.BUCKET_NAME, 'test-database')

print(example)

# Delete specific Blob
Database.delete(config.BUCKET_NAME, 'test-database')

# Delete all
Database.delete_all(config.BUCKET_NAME)
