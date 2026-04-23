require 'minitest/autorun'
require 'rack/test'
require_relative '../app'

class AppTest < Minitest::Test
  include Rack::Test::Methods

  def app
    Sinatra::Application
  end

  def test_health_route
    get '/'
    assert_equal 200, last_response.status
    assert_includes last_response.body, '{{project_name}}'
  end
end
