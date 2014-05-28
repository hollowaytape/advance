FactoryGirl.define do
  factory :user do
    name "Max Silbiger"
    email "max.silbiger@gmail.com"
    password "foobar"
    password_confirmation "foobar"
  end
end