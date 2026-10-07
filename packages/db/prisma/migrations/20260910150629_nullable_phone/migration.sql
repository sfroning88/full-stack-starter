-- DropIndex
DROP INDEX "iam"."users_phone_key";

-- AlterTable
ALTER TABLE "iam"."users" ALTER COLUMN "phone" DROP NOT NULL;
