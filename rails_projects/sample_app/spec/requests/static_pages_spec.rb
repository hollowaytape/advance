require 'spec_helper'

describe "Static Pages" do

    describe "Home Page" do
        
        it "should have the content 'Sample App'" do
            visit '/static_pages/home'
            expect(page).to have_content('Sample App')
        end
        
        it "should have the right title" do
            visit '/static_pages/home'
            expect(page).to have_title("Ruby on Rails Tutorial Sample App | Home")
        end
        
        it "should not have a custom page title" do
            visit 'static_pages/home'
            expect(page).not_to_have_title('| Home')
        end
    end
    
    describe "Help Page" do
    
        it "should have the content 'Help'" do
            visit '/static_pages/help'
            expect(page).to have_content('Help')
        end
        
        it "should have the right title" do
            visit '/static_pages/help'
            expect(page).to have_title("Ruby on Rails Tutorial Sample App | Help")
        end
    end
    
    describe "About Page" do
    
        it "should have the content 'About'" do
            visit '/static_pages/about'
            expect(page).to have_content('About')
        end
        
        it "should have the right title" do
            visit '/static_pages/about'
            expect(page).to have_title("Ruby on Rails Tutorial Sample App | About Us")
        end
    end
    
end