require 'sinatra'
require 'json'

require_relative './lib/config'
require_relative './lib/db'

configure do
  set :bind, '0.0.0.0'
  set :port, AppConfig.port
end

USERS = []
NEXT_ID = { value: 1 }

get '/health' do
  content_type :json
  { status: 'ok', project: '{{project_name}}', env: AppConfig.env }.to_json
end

get '/users' do
  content_type :json
  USERS.to_json
end

get '/users/:id' do
  content_type :json
  user = USERS.find { |item| item[:id] == params[:id].to_i }
  halt 404, { error: 'User not found' }.to_json if user.nil?
  user.to_json
end

post '/users' do
  payload = JSON.parse(request.body.read)
  name = payload['name'].to_s.strip
  email = payload['email'].to_s.strip
  halt 400, { error: 'Invalid name or email' }.to_json if name.length < 2 || !email.include?('@')

  user = { id: NEXT_ID[:value], name: name, email: email.downcase }
  NEXT_ID[:value] += 1
  USERS << user

  status 201
  content_type :json
  user.to_json
end

put '/users/:id' do
  payload = JSON.parse(request.body.read)
  name = payload['name'].to_s.strip
  email = payload['email'].to_s.strip
  halt 400, { error: 'Invalid name or email' }.to_json if name.length < 2 || !email.include?('@')

  user = USERS.find { |item| item[:id] == params[:id].to_i }
  halt 404, { error: 'User not found' }.to_json if user.nil?

  user[:name] = name
  user[:email] = email.downcase
  content_type :json
  user.to_json
end

delete '/users/:id' do
  index = USERS.find_index { |item| item[:id] == params[:id].to_i }
  halt 404, { error: 'User not found' }.to_json if index.nil?
  USERS.delete_at(index)
  content_type :json
  { status: 'deleted' }.to_json
end
