class Micropost < ActiveRecord::Base
  belongs_to :user
  default_scope -> { order('created_at DESC') } # lambda, SQL for "descending."
  validates :user_id, presence: true
  validates :content, presence: true, length: { maximum: 140 }
end
