/**
 * Global Audio Manager for background music — with YouTube genre switching
 */

// Genre definitions with YouTube video IDs
export const MUSIC_GENRES = [
    {
        id: 'ambient',
        name: 'Ambient',
        description: 'Chill atmospheric',
        color: '#38BDF8',
        useLocalTrack: false,
        localSrc: '/sounds/cfl_turningpages-belem-breeze-487596.ogg',
        ytIds: ['Vqe0kDQ06H8']
    },
    {
        id: 'phonk',
        name: 'Phonk',
        description: '2026 trending beats',
        color: '#A78BFA',
        useLocalTrack: false,
        ytIds: ['bHqGOcZX7-o']
    },
    {
        id: 'lofi',
        name: 'Lo-Fi',
        description: 'Chill coding vibes',
        color: '#7C3AED',
        useLocalTrack: false,
        ytIds: ['KBdUsYn68Tw']
    },
    {
        id: 'cyberpunk',
        name: 'Electric Guitar',
        description: 'Electric phonk songs',
        color: '#06B6D4',
        useLocalTrack: false,
        ytIds: ['kEM9taB4LRo', 'GGmMCTN5bSc']
    },
    {
        id: 'off',
        name: 'Silent',
        description: 'No music',
        color: '#6B7280',
        useLocalTrack: false,
        ytIds: []
    }
];

let bgMusicAudio = null;
let isMuted = false;
let bgMusicStarted = false;
let currentGenreId = 'ambient';
let currentTrackIndex = 0;
let ytPlayerRef = null; // Will be set by NavigationUI

// Register the YouTube player reference — stop old one first
export const setYTPlayer = (player) => {
    if (ytPlayerRef && ytPlayerRef !== player) {
        try { ytPlayerRef.stopVideo(); } catch (e) {}
    }
    ytPlayerRef = player;
};

// Force stop the current YT player
export const destroyYTPlayer = () => {
    if (ytPlayerRef) {
        try { ytPlayerRef.stopVideo(); } catch (e) {}
        ytPlayerRef = null;
    }
};

export const getYTPlayer = () => ytPlayerRef;

// Initialize background music (local audio only for ambient)
export const initAudio = () => {
    if (typeof window === 'undefined') return;

    const savedMuted = localStorage.getItem('audio_muted');
    isMuted = savedMuted === 'true';

    const savedGenre = localStorage.getItem('symbiote-music-genre');
    if (savedGenre) currentGenreId = savedGenre;

    if (!bgMusicAudio) {
        bgMusicAudio = new Audio('/sounds/cfl_turningpages-belem-breeze-487596.ogg');
        bgMusicAudio.preload = 'auto';
        bgMusicAudio.loop = true;
        bgMusicAudio.volume = 0.3;
        bgMusicAudio.muted = isMuted;
        bgMusicAudio.load();
    }
};

export const playBackgroundMusic = () => {
    initAudio();
    bgMusicStarted = true;
    const genre = MUSIC_GENRES.find(g => g.id === currentGenreId);

    if (genre && genre.useLocalTrack) {
        // Play local audio
        if (bgMusicAudio && bgMusicAudio.paused) {
            bgMusicAudio.play().catch(() => {});
        }
    }
    // YouTube playback is handled by the React component
};

export const pauseBackgroundMusic = () => {
    if (bgMusicAudio && !bgMusicAudio.paused) {
        bgMusicAudio.pause();
    }
    // Pause YT if active
    if (ytPlayerRef) {
        try { ytPlayerRef.pauseVideo(); } catch (e) {}
    }
};

export const switchGenre = (genreId) => {
    // ALWAYS stop everything first before switching
    if (bgMusicAudio) bgMusicAudio.pause();
    destroyYTPlayer();

    currentGenreId = genreId;
    currentTrackIndex = 0;
    localStorage.setItem('symbiote-music-genre', genreId);

    const genre = MUSIC_GENRES.find(g => g.id === genreId);

    if (genreId === 'off') {
        // Everything already stopped above
    } else if (genre && genre.useLocalTrack) {
        // Play local track
        if (bgMusicAudio) {
            bgMusicAudio.src = genre.localSrc;
            bgMusicAudio.loop = true;
            const vol = bgMusicAudio.volume;
            bgMusicAudio.volume = vol;
            if (bgMusicStarted) bgMusicAudio.play().catch(() => {});
        }
    }
    // For YouTube genres: React component will mount new player via genreChanged event

    window.dispatchEvent(new CustomEvent('genreChanged', { detail: genreId }));
};

export const getCurrentGenre = () => currentGenreId;
export const getCurrentTrackIndex = () => currentTrackIndex;
export const setCurrentTrackIndex = (i) => { currentTrackIndex = i; };
export const isStarted = () => bgMusicStarted;

export const nextTrack = () => {
    const genre = MUSIC_GENRES.find(g => g.id === currentGenreId);
    if (genre && genre.ytIds.length > 1) {
        currentTrackIndex = (currentTrackIndex + 1) % genre.ytIds.length;
        window.dispatchEvent(new CustomEvent('trackChanged', { detail: currentTrackIndex }));
    }
};

export const toggleMute = () => {
    isMuted = !isMuted;
    if (bgMusicAudio) bgMusicAudio.muted = isMuted;
    if (ytPlayerRef) {
        try {
            if (isMuted) ytPlayerRef.mute();
            else ytPlayerRef.unMute();
        } catch (e) {}
    }
    return isMuted;
};

export const getIsMuted = () => isMuted;

export const setMusicVolume = (vol) => {
    if (bgMusicAudio) {
        bgMusicAudio.volume = Math.max(0, Math.min(1, vol));
        if (vol > 0 && isMuted) {
            isMuted = false;
            bgMusicAudio.muted = false;
        }
        if (vol > 0 && bgMusicAudio.paused && bgMusicStarted && currentGenreId !== 'off') {
            const genre = MUSIC_GENRES.find(g => g.id === currentGenreId);
            if (genre && genre.useLocalTrack) bgMusicAudio.play().catch(() => {});
        }
    }
    // Set YT volume too
    if (ytPlayerRef) {
        try { ytPlayerRef.setVolume(vol * 100); } catch (e) {}
    }
    window.dispatchEvent(new CustomEvent('musicVolumeChanged', { detail: vol }));
};

export const getMusicVolume = () => {
    return bgMusicAudio ? bgMusicAudio.volume : 0.3;
};
