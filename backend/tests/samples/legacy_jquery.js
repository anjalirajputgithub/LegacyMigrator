// Legacy jQuery-style code — candidate migration target: jQuery -> React
var UserList = function(containerId) {
  this.containerId = containerId;
  this.users = [];
};

UserList.prototype.fetchUsers = function() {
  var self = this;
  $.ajax({
    url: '/api/users',
    method: 'GET',
    success: function(data) {
      self.users = data;
      self.render();
    },
    error: function(err) {
      console.log('Failed to fetch users: ' + err);
    }
  });
};

UserList.prototype.render = function() {
  var container = $('#' + this.containerId);
  container.empty();
  for (var i = 0; i < this.users.length; i++) {
    var user = this.users[i];
    container.append('<div class="user">' + user.name + '</div>');
  }
};

$(document).ready(function() {
  var list = new UserList('user-list');
  list.fetchUsers();
});
