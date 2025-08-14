import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Import UI components
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { Alert, AlertDescription } from './components/ui/alert';
import { Search, Plus, Edit2, Trash2, User, LogOut, Eye, EyeOff } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Validation utilities
const validateDiscordUserId = (id) => {
  if (!id || !id.trim()) return "Discord User ID is required";
  const trimmedId = id.trim();
  if (!trimmedId.match(/^\d+$/)) return "Discord User ID must contain only numbers";
  if (trimmedId.length < 17 || trimmedId.length > 19) return "Discord User ID must be 17-19 digits long";
  if (parseInt(trimmedId) < 100000000000000000) return "Invalid Discord User ID - please check your ID";
  return null;
};

const validateUsername = (username) => {
  if (!username || !username.trim()) return "Username is required";
  const trimmed = username.trim();
  if (trimmed.length < 2) return "Username must be at least 2 characters long";
  if (trimmed.length > 32) return "Username must be no more than 32 characters long";
  return null;
};

const validatePassword = (password) => {
  if (!password) return "Password is required";
  if (password.length < 6) return "Password must be at least 6 characters long";
  return null;
};

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (discordUserId, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        discord_user_id: discordUserId,
        password: password
      });
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setToken(access_token);
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
                          (error.response?.data?.detail && Array.isArray(error.response.data.detail) 
                            ? error.response.data.detail.map(e => e.msg).join(', ')
                            : 'Login failed');
      return { success: false, error: errorMessage };
    }
  };

  const register = async (discordUserId, username, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        discord_user_id: discordUserId,
        username: username,
        password: password
      });
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setToken(access_token);
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
                          (error.response?.data?.detail && Array.isArray(error.response.data.detail) 
                            ? error.response.data.detail.map(e => e.msg).join(', ')
                            : 'Registration failed');
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, token, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Component
const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [discordUserId, setDiscordUserId] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const validateForm = () => {
    const errors = {};
    
    const discordIdError = validateDiscordUserId(discordUserId);
    if (discordIdError) errors.discordUserId = discordIdError;
    
    if (!isLogin) {
      const usernameError = validateUsername(username);
      if (usernameError) errors.username = usernameError;
    }
    
    const passwordError = validatePassword(password);
    if (passwordError) errors.password = passwordError;
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    let result;
    if (isLogin) {
      result = await login(discordUserId.trim(), password);
    } else {
      result = await register(discordUserId.trim(), username.trim(), password);
    }

    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setFieldErrors({});
    setDiscordUserId('');
    setUsername('');
    setPassword('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-900">
            Discord Notes
          </CardTitle>
          <CardDescription>
            {isLogin ? 'Sign in to your account' : 'Create a new account'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Discord User ID *
              </label>
              <Input
                type="text"
                value={discordUserId}
                onChange={(e) => {
                  setDiscordUserId(e.target.value);
                  if (fieldErrors.discordUserId) {
                    setFieldErrors(prev => ({ ...prev, discordUserId: null }));
                  }
                }}
                placeholder="123456789012345678"
                required
                className={fieldErrors.discordUserId ? 'border-red-500' : ''}
              />
              {fieldErrors.discordUserId && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.discordUserId}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Find this in Discord: Settings → Advanced → Developer Mode → Right-click your name → Copy ID
              </p>
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username *
                </label>
                <Input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (fieldErrors.username) {
                      setFieldErrors(prev => ({ ...prev, username: null }));
                    }
                  }}
                  placeholder="Your display name"
                  required={!isLogin}
                  className={fieldErrors.username ? 'border-red-500' : ''}
                />
                {fieldErrors.username && (
                  <p className="text-red-500 text-xs mt-1">{fieldErrors.username}</p>
                )}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password *
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (fieldErrors.password) {
                      setFieldErrors(prev => ({ ...prev, password: null }));
                    }
                  }}
                  placeholder="Your password"
                  required
                  className={fieldErrors.password ? 'border-red-500 pr-10' : 'pr-10'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.password}</p>
              )}
              {!isLogin && (
                <p className="text-xs text-gray-500 mt-1">
                  Must be at least 6 characters long
                </p>
              )}
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
            </Button>
          </form>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={toggleMode}
              className="text-sm text-blue-500 hover:text-blue-700"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Notes Dashboard Component
const Dashboard = () => {
  const [notes, setNotes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [editContent, setEditContent] = useState('');
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async (search = '') => {
    try {
      setLoading(search === '');
      setSearchLoading(search !== '');
      const params = search ? { search } : {};
      const response = await axios.get(`${API}/notes`, { params });
      setNotes(response.data);
    } catch (error) {
      console.error('Failed to fetch notes:', error);
    } finally {
      setLoading(false);
      setSearchLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchNotes(searchTerm);
  };

  const handleEdit = (note) => {
    setEditingNote(note.id);
    setEditContent(note.content);
  };

  const handleSaveEdit = async (noteId) => {
    try {
      await axios.put(`${API}/notes/${noteId}`, {
        content: editContent
      });
      setEditingNote(null);
      fetchNotes(searchTerm);
    } catch (error) {
      console.error('Failed to update note:', error);
    }
  };

  const handleDelete = async (noteId) => {
    if (window.confirm('Are you sure you want to delete this note?')) {
      try {
        await axios.delete(`${API}/notes/${noteId}`);
        fetchNotes(searchTerm);
      } catch (error) {
        console.error('Failed to delete note:', error);
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Discord Notes</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user?.username}</span>
                <span className="text-xs text-gray-400">({user?.discord_user_id})</span>
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search */}
        <div className="mb-8">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search your notes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" disabled={searchLoading}>
              {searchLoading ? 'Searching...' : 'Search'}
            </Button>
            {searchTerm && (
              <Button 
                variant="outline" 
                onClick={() => {
                  setSearchTerm('');
                  fetchNotes();
                }}
              >
                Clear
              </Button>
            )}
          </form>
        </div>

        {/* Stats */}
        <div className="mb-6">
          <p className="text-sm text-gray-600">
            {searchTerm ? `Found ${notes.length} notes matching "${searchTerm}"` : `${notes.length} total notes`}
          </p>
        </div>

        {/* Notes List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <p className="text-gray-500">Loading notes...</p>
            </div>
          ) : notes.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">
                {searchTerm ? 'No notes found matching your search.' : 'No notes yet. Start taking notes with your Discord bot!'}
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Use commands like <code className="bg-gray-100 px-1 rounded">!note add Your note here</code> in Discord
              </p>
            </div>
          ) : (
            notes.map((note) => (
              <Card key={note.id} className="w-full">
                <CardContent className="pt-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      {editingNote === note.id ? (
                        <div className="space-y-2">
                          <Textarea
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="min-h-[100px]"
                          />
                          <div className="flex gap-2">
                            <Button size="sm" onClick={() => handleSaveEdit(note.id)}>
                              Save
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setEditingNote(null)}>
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <p className="text-gray-900 whitespace-pre-wrap mb-2">{note.content}</p>
                          <div className="flex flex-wrap gap-2">
                            {note.server_name && (
                              <Badge variant="secondary">
                                Server: {note.server_name}
                              </Badge>
                            )}
                            {note.channel_name && (
                              <Badge variant="outline">
                                #{note.channel_name}
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    {editingNote !== note.id && (
                      <div className="flex gap-2 ml-4">
                        <Button size="sm" variant="ghost" onClick={() => handleEdit(note)}>
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDelete(note.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    <span className="font-medium">ID:</span> {note.id.substring(0, 8)}... • 
                    <span className="font-medium"> Created:</span> {formatDate(note.created_at)}
                    {note.updated_at !== note.created_at && (
                      <span> • <span className="font-medium">Updated:</span> {formatDate(note.updated_at)}</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </main>
    </div>
  );
};

// Main App Component
const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route path="/" element={<AppRouter />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};

const AppRouter = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return user ? <Dashboard /> : <Auth />;
};

export default App;