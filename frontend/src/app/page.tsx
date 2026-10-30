'use client';

import React, { useState, useEffect, useRef } from 'react';

interface TripFormState {
  origin: string;
  destination: string;
  startDate: string;
  endDate: string;
  travelers: number;
  interests: string[];
  budgetInr: number;
}

interface Destination {
  id: string;
  name: string;
  state_ut: string;
  district_city: string;
  category: string;
}

const AVAILABLE_INTERESTS = [
  'Heritage & History',
  'Beaches & Coastal',
  'Mountains & Trekking',
  'Wildlife & Nature',
  'Spiritual & Wellness',
  'Culinary & Food',
  'Adventure Sports',
];

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [formState, setFormState] = useState<TripFormState>({
    origin: 'Delhi',
    destination: 'Jaipur',
    startDate: '',
    endDate: '',
    travelers: 2,
    interests: ['Heritage & History'],
    budgetInr: 50000,
  });

  // Destination autocomplete state
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [activeSearchField, setActiveSearchField] = useState<'origin' | 'destination' | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchingDest, setIsSearchingDest] = useState(false);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<any | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [isFetchingRecs, setIsFetchingRecs] = useState<boolean>(false);
  const [recError, setRecError] = useState<string | null>(null);
  const [datasetInfo, setDatasetInfo] = useState<any>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetch(`${apiUrl}/health`)
      .then((res) => {
        if (res.ok) {
          setBackendStatus('connected');
          // Fetch dataset status mode
          return fetch(`${apiUrl}/api/dataset-status`);
        } else {
          setBackendStatus('disconnected');
          throw new Error('Backend disconnected');
        }
      })
      .then((res) => res.json())
      .then((data) => setDatasetInfo(data))
      .catch(() => {
        setBackendStatus('disconnected');
      });
  }, [apiUrl]);

  // Fetch destinations when typing in origin or destination
  useEffect(() => {
    if (!activeSearchField) {
      setDestinations([]);
      return;
    }

    setIsSearchingDest(true);
    const timer = setTimeout(() => {
      fetch(`${apiUrl}/api/destinations?query=${encodeURIComponent(searchQuery)}&limit=10`)
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => {
          setDestinations(data);
          setIsSearchingDest(false);
        })
        .catch(() => {
          setDestinations([]);
          setIsSearchingDest(false);
        });
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery, activeSearchField, apiUrl]);

  const handleInterestToggle = (interest: string) => {
    setFormState((prev) => {
      const exists = prev.interests.includes(interest);
      if (exists) {
        return { ...prev, interests: prev.interests.filter((i) => i !== interest) };
      } else {
        return { ...prev, interests: [...prev.interests, interest] };
      }
    });
  };

  const handleSelectDestination = (destName: string) => {
    if (activeSearchField === 'origin') {
      setFormState((prev) => ({ ...prev, origin: destName }));
    } else if (activeSearchField === 'destination') {
      setFormState((prev) => ({ ...prev, destination: destName }));
    }
    setActiveSearchField(null);
    setSearchQuery('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessResult(null);

    // Validation
    if (!formState.origin.trim() || !formState.destination.trim()) {
      setErrorMsg('Origin and destination are required.');
      return;
    }
    if (!formState.startDate || !formState.endDate) {
      setErrorMsg('Journey start and end dates are required.');
      return;
    }
    if (new Date(formState.endDate) < new Date(formState.startDate)) {
      setErrorMsg('Journey end date cannot be earlier than start date.');
      return;
    }
    if (formState.travelers <= 0) {
      setErrorMsg('Number of travelers must be greater than zero.');
      return;
    }
    if (formState.budgetInr <= 0) {
      setErrorMsg('Budget in INR must be greater than zero.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch(`${apiUrl}/api/trip/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          origin: formState.origin,
          destination: formState.destination,
          start_date: formState.startDate,
          end_date: formState.endDate,
          travelers: formState.travelers,
          interests: formState.interests,
          budget_inr: formState.budgetInr,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail ? JSON.stringify(errorData.detail) : 'Failed to validate trip search');
      }

      const data = await res.json();
      setSuccessResult(data);

      // Fetch recommendations for destination & interests
      setIsFetchingRecs(true);
      setRecError(null);
      try {
        const recRes = await fetch(`${apiUrl}/api/recommendations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            destination: formState.destination,
            origin: formState.origin,
            interests: formState.interests,
            limit: 6,
          }),
        });
        if (!recRes.ok) {
          throw new Error('Failed to fetch recommendations');
        }
        const recData = await recRes.json();
        setRecommendations(recData.recommendations || []);
      } catch (recErr: any) {
        setRecError(recErr.message || 'Error fetching recommendations');
        setRecommendations([]);
      } finally {
        setIsFetchingRecs(false);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'An error occurred connecting to the backend.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-r from-orange-500 to-green-600 text-white font-bold px-3 py-1.5 rounded-lg shadow">
              ITA
            </div>
            <div>
              <span className="font-bold text-xl text-slate-900 tracking-tight">IndiaTravelAgent</span>
              <span className="hidden sm:inline-block ml-2 text-xs bg-amber-100 text-amber-800 font-medium px-2 py-0.5 rounded-full" title={datasetInfo?.license || "Development Fixture"}>
                {datasetInfo?.dataset_mode || 'Development Fixture'}
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs font-medium">
              <span className="text-slate-500">Backend API:</span>
              {backendStatus === 'checking' && (
                <span className="bg-amber-100 text-amber-800 px-2 py-1 rounded-full flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                  Checking...
                </span>
              )}
              {backendStatus === 'connected' && (
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  Connected ({apiUrl})
                </span>
              )}
              {backendStatus === 'disconnected' && (
                <span className="bg-rose-100 text-rose-800 px-2 py-1 rounded-full flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                  Offline
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white py-16 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#ff9933_1px,transparent_1px)] [background-size:16px_16px]"></div>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Explore India with Verified Destination Data
          </h1>
          <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-8">
            Plan intelligent itineraries across Indian states and union territories backed by verified OpenStreetMap attraction datasets.
          </p>
        </div>
      </section>

      {/* Main Content & Search Form */}
      <main className="flex-grow max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-20 pb-16">
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6 sm:p-10">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900">Plan Your Indian Adventure</h2>
            <p className="text-sm text-slate-500">Search verified destinations or enter your custom trip parameters below.</p>
          </div>

          {errorMsg && (
            <div className="mb-6 bg-rose-50 border-l-4 border-rose-500 p-4 rounded-r-lg text-rose-700 text-sm">
              <span className="font-semibold">Validation Error:</span> {errorMsg}
            </div>
          )}

          {successResult && (
            <div className="mb-8 space-y-6">
              <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-r-lg text-green-800 text-sm">
                <span className="font-semibold">Success!</span> {successResult.message}
                <div className="mt-2 text-xs bg-white p-3 rounded border border-green-200 font-mono overflow-x-auto">
                  {JSON.stringify(successResult.search_parameters, null, 2)}
                </div>
              </div>

              {/* Recommendation Engine UI */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-2">
                  <div>
                    <h3 className="text-xl font-bold text-slate-900">
                      Recommended Attractions in {formState.destination}
                    </h3>
                    <p className="text-xs text-slate-500">Ranked by content relevance and your selected interests</p>
                  </div>
                  <span className="bg-orange-100 text-orange-800 text-xs font-semibold px-3 py-1 rounded-full">
                    AI Content-Based Engine
                  </span>
                </div>

                {isFetchingRecs ? (
                  <div className="py-12 text-center text-slate-500">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-3"></div>
                    Generating ranked recommendations...
                  </div>
                ) : recError ? (
                  <div className="p-4 bg-rose-50 text-rose-700 rounded-lg text-sm border border-rose-200">
                    {recError}
                  </div>
                ) : recommendations.length === 0 ? (
                  <div className="py-8 text-center text-slate-500 text-sm">
                    No recommendations found for "{formState.destination}" with the selected interests. Try selecting different interests or destination!
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {recommendations.map((item, idx) => (
                      <div key={item.attraction.id || idx} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:border-orange-300 transition flex flex-col justify-between">
                        <div>
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-bold text-slate-900 text-base">{item.attraction.name}</h4>
                            <span className="bg-orange-100 text-orange-800 text-xs font-semibold px-2 py-0.5 rounded-full">
                              {item.attraction.category}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mb-2">
                            📍 {item.attraction.district_city}, {item.attraction.state_ut}
                          </p>
                          <p className="text-sm text-slate-700 mb-4 line-clamp-3">
                            {item.attraction.description}
                          </p>
                        </div>
                        <div className="border-t border-slate-100 pt-3 mt-auto">
                          <div className="flex justify-between items-center text-xs text-slate-600 mb-1">
                            <span className="font-medium">Relevance Score:</span>
                            <span className="font-bold text-orange-600">{(item.relevance_score * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-xs text-slate-500 italic bg-slate-50 p-2 rounded border border-slate-100">
                            💡 {item.reason}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 relative">
              {/* Origin */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Origin City / State</label>
                <input
                  type="text"
                  value={formState.origin}
                  onChange={(e) => {
                    setFormState({ ...formState, origin: e.target.value });
                    setSearchQuery(e.target.value);
                    setActiveSearchField('origin');
                  }}
                  onFocus={() => {
                    setActiveSearchField('origin');
                    setSearchQuery(formState.origin);
                  }}
                  placeholder="e.g. Mumbai, Delhi, Bengaluru"
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                  required
                />
              </div>

              {/* Destination */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Destination in India</label>
                <input
                  type="text"
                  value={formState.destination}
                  onChange={(e) => {
                    setFormState({ ...formState, destination: e.target.value });
                    setSearchQuery(e.target.value);
                    setActiveSearchField('destination');
                  }}
                  onFocus={() => {
                    setActiveSearchField('destination');
                    setSearchQuery(formState.destination);
                  }}
                  placeholder="e.g. Jaipur, Goa, Munnar"
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                  required
                />
              </div>

              {/* Autocomplete Dropdown */}
              {activeSearchField && (
                <div className="absolute top-20 z-30 left-0 right-0 sm:right-1/2 bg-white rounded-xl shadow-2xl border border-slate-200 max-h-64 overflow-y-auto p-2">
                  <div className="px-3 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider flex justify-between">
                    <span>Verified Destinations ({activeSearchField})</span>
                    <button
                      type="button"
                      onClick={() => setActiveSearchField(null)}
                      className="text-slate-500 hover:text-slate-700"
                    >
                      Close ✕
                    </button>
                  </div>
                  {isSearchingDest ? (
                    <div className="px-3 py-3 text-sm text-slate-500 text-center">Searching database...</div>
                  ) : destinations.length === 0 ? (
                    <div className="px-3 py-3 text-sm text-slate-500 text-center">No matching destinations found.</div>
                  ) : (
                    destinations.map((d) => (
                      <div
                        key={d.id}
                        onClick={() => handleSelectDestination(d.name)}
                        className="px-3 py-2 hover:bg-orange-50 rounded-lg cursor-pointer transition flex justify-between items-center text-sm"
                      >
                        <div>
                          <span className="font-semibold text-slate-900">{d.name}</span>
                          <span className="text-xs text-slate-500 ml-2">({d.district_city}, {d.state_ut})</span>
                        </div>
                        <span className="text-xs bg-orange-100 text-orange-800 px-2 py-0.5 rounded-full font-medium">
                          {d.category}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              {/* Start Date */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Journey Start Date</label>
                <input
                  type="date"
                  value={formState.startDate}
                  onChange={(e) => setFormState({ ...formState, startDate: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                  required
                />
              </div>

              {/* End Date */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Journey End Date</label>
                <input
                  type="date"
                  value={formState.endDate}
                  onChange={(e) => setFormState({ ...formState, endDate: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                  required
                />
              </div>

              {/* Travelers */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Number of Travelers</label>
                <input
                  type="number"
                  min="1"
                  value={formState.travelers}
                  onChange={(e) => setFormState({ ...formState, travelers: parseInt(e.target.value) || 1 })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                  required
                />
              </div>
            </div>

            {/* Budget */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Total Budget (INR ₹)</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-4 flex items-center text-slate-500 font-semibold">₹</span>
                <input
                  type="number"
                  min="1000"
                  step="500"
                  value={formState.budgetInr}
                  onChange={(e) => setFormState({ ...formState, budgetInr: parseFloat(e.target.value) || 0 })}
                  className="w-full rounded-lg border border-slate-300 pl-8 pr-4 py-2.5 text-slate-900 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                  required
                />
              </div>
            </div>

            {/* Interests */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Interests & Activities</label>
              <div className="flex flex-wrap gap-2">
                {AVAILABLE_INTERESTS.map((interest) => {
                  const selected = formState.interests.includes(interest);
                  return (
                    <button
                      key={interest}
                      type="button"
                      onClick={() => handleInterestToggle(interest)}
                      className={`px-3.5 py-1.5 rounded-full text-sm font-medium transition ${
                        selected
                          ? 'bg-orange-600 text-white shadow-sm'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {selected ? '✓ ' : '+ '} {interest}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold py-3.5 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50"
              >
                {isSubmitting ? 'Validating Trip Search...' : 'Generate AI Travel Itinerary'}
              </button>
            </div>
          </form>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          IndiaTravelAgent &copy; 2026. Powered by OpenStreetMap Open Database License (ODbL).
        </div>
      </footer>
    </div>
  );
}
