module AppConfig
  module_function

  def env
    ENV.fetch('APP_ENV', 'development')
  end

  def port
    ENV.fetch('PORT', 4567)
  end

  def database_url
    ENV.fetch('DATABASE_URL', 'sqlite://data/app.db')
  end
end
