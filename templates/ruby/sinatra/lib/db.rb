require_relative './config'

module DatabaseClient
  module_function

  def url
    AppConfig.database_url
  end
end
