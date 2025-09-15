import m3u8
import pathlib
import itertools
import datetime
from collections import deque
import time
from multiprocessing import Process


class SegmentLink:
    """handles one symlink to a segment"""

    def __init__(
        self,
        dst_dir: pathlib.Path,
        res: str,
        seq: int,
        segment: m3u8.Segment,
        dry_run: bool = False
        ):
        self.link = dst_dir / f"{res}_{seq:09}.ts"
        self.target = pathlib.Path(segment.absolute_uri)
        self.segment = segment
        self.dry_run = dry_run

    @property
    def filename(self):  # keep compatibility
        return self.link.name

    def ln(self):
        if self.dry_run:
            print(f"linking: {self.link} -> {self.target}")
            return
        if self.link.exists() or self.link.is_symlink():
            self.link.unlink()
        self.link.symlink_to(self.target)

    def rm(self):
        if self.dry_run:
            print(f"removing: {self.link}")
            return
        try:
            self.link.unlink()
        except FileNotFoundError:
            pass


class SegmentCycle:
    """
    Creates infinite list of segments,
    updates the seq and time,
    and tracks what segments are to be linked/unlinked
    """

    # TODO: need discontinuity at max_seq

    # how many loops before segment filenames reset?
    # for 6 second segments, this should last 190 years
    # not my problem after that :)
    max_seq = 999_999_999

    def __init__(
        self,
        output_dir: pathlib.Path,
        segments: m3u8.SegmentList,
        window_count: int,
        alive_count: int,
        res: str,
        start_date_time: datetime.datetime,
        dry_run: bool = False,
    ):
        assert alive_count >= window_count, f"alive_count ({alive_count}) was smaller than window_count ({window_count})"

        self.window_count = window_count
        self.alive_count = alive_count
        self.start_date_time = start_date_time

        # infinitely cycling segments in loop
        self.seg_cycle = (
            SegmentLink(
                dst_dir=output_dir,
                res=res,
                seq=seq,
                segment=segment,
                dry_run=dry_run
                )
            for seq, segment in zip(
                itertools.cycle(range(0, self.max_seq + 1)),
                itertools.cycle(segments),
            )
        )

    def __iter__(self):

        # playlist that is unfilled has negative seq
        self.media_sequence = -self.window_count

        # time tracking
        self.program_date_time = self.start_date_time

        # for segements still "alive" on disk
        self.alive_seg_links = deque(maxlen=self.alive_count)
        # for hls playlist window
        # this is a list of segments, not a SegmentList
        self._window_segs = deque(maxlen=self.window_count)
        
        # for adding/deleting segments
        self.del_seg_links = []
        self.add_seg_links = []

        return self

    def __next__(self):
        
        # get next segment
        next_seg_link = next(self.seg_cycle)
        self.media_sequence += 1

        while len(self.alive_seg_links) >= self.alive_count:
            del_seg_link = self.alive_seg_links.popleft()
            self.del_seg_links.append(del_seg_link)
        self.alive_seg_links.append(next_seg_link)
        self.add_seg_links.append(next_seg_link)

        # build new segment
        base_seg = next_seg_link.segment
        self.program_date_time += datetime.timedelta(seconds=base_seg.duration)

        new_seg = m3u8.Segment(
            uri=next_seg_link.filename,
            program_date_time=self.program_date_time,
            duration=base_seg.duration,
            discontinuity=base_seg.discontinuity,
        )

        self._window_segs.append(new_seg)
        return self

    @property
    def window_segs(self):
        return m3u8.SegmentList(self._window_segs)

    def ln_segments(self):
        for seg_link in self.add_seg_links:
            seg_link.ln()
        self.add_seg_links.clear()

    def rm_segments(self):
        for seg_link in self.del_seg_links:
            seg_link.rm()
        self.del_seg_links.clear()

    def manage_segments(self):
        self.rm_segments()
        self.ln_segments()


class HLSPlaylist:

    def __init__(
        self,
        vod_playlist_path: pathlib.Path,
        output_dir: pathlib.Path,
        res: str,
        window_count: int,
        start_date_time: datetime.datetime,
        seq_limit: int = None,
        dry_run: bool = False,
    ):
        self.vod_playlist_path = vod_playlist_path
        self.output_dir = output_dir
        self.res = res
        self.start_date_time = start_date_time
        self.playlist_filename = f"{res}.m3u8"
        self.output_path = output_dir / self.playlist_filename
        self.window_count = window_count
        self.alive_count = 2 * self.window_count
        self.seq_limit = seq_limit
        self.dry_run = dry_run

        # load data
        self.original_playlist = m3u8.load(str(self.vod_playlist_path))
        self.version = self.original_playlist.version

        # TODO: parameterize which segments to use, not hardcode
        self.segments = self.original_playlist.segments
        self.segments[0].discontinuity = True
        
        # set start time in past so that first playlist is full
        first_window_segments = self.segments[: self.window_count]
        past_dur = sum(seg.duration for seg in first_window_segments)
        self.past_start_date = self.start_date_time - datetime.timedelta(seconds=past_dur)

    @property
    def media_sequence(self) -> int:
        return self.seg_cycle.media_sequence

    @property
    def playlist(self) -> m3u8.M3U8:
        new_playlist = m3u8.M3U8()
        new_playlist.media_sequence = self.media_sequence
        new_playlist.target_duration = self.original_playlist.target_duration
        new_playlist.version = self.original_playlist.version
        new_playlist.segments = self.seg_cycle.window_segs
        return new_playlist
        
    def __iter__(self):

        # create the segment iterator
        self.seg_cycle = iter(
            SegmentCycle(
                output_dir=self.output_dir,
                segments=self.segments,
                window_count=self.window_count,
                alive_count=self.alive_count,
                res=self.res,
                start_date_time=self.past_start_date,
                dry_run=self.dry_run,
            )
        )

        # fast-forward to first full playlist
        for _ in range(self.window_count - 1):
            next(self.seg_cycle)

        return self

    def __next__(self):

        # iterate sequence, stop if limit reached
        next(self.seg_cycle)
        if self.seq_limit and self.media_sequence >= self.seq_limit:
            raise StopIteration
        
        return self
    
    def clear_hls_dir(self):
        for pattern in ("*.ts", "*.m3u8"):
            for hls_file in self.output_dir.glob(pattern):
                hls_file.unlink()
                print(f"Deleted {hls_file}")

    def write_playlist(self):
        if self.dry_run:
            print(self.playlist.dumps(infspec="microseconds"))
        else:
            self.output_path.write_text(self.playlist.dumps(infspec="microseconds"))

    def sleep_and_write(self):
        release_date_time = self.seg_cycle.program_date_time
        wait_sec = (release_date_time - datetime.datetime.now()).total_seconds()

        # if we missed the publishing window, fast-forward ahead
        if wait_sec > 0:
            time.sleep(wait_sec)
        else:
            print(f"[WARN] Missed deadline by {-wait_sec:.3f}s, fast-forwarding...")
        self.seg_cycle.manage_segments()
        self.write_playlist()


def run_playlist(playlist):
    playlist.clear_hls_dir()
    for _ in playlist:
        playlist.sleep_and_write()

if __name__ == "__main__":
    print("starting script...")


    base_dir = pathlib.Path("/hls/streams")
    src_dir  = pathlib.Path("/hls/streams-original")
    window_count = 6
    start_date_time = datetime.datetime.now() + datetime.timedelta(seconds=1)
    dry_run = False

    channels = {
        "TEST_CHANNEL_A_360p": ("TEST_CHANNEL_A", "360p"),
        "TEST_CHANNEL_B_360p": ("TEST_CHANNEL_B", "360p"),
    }

    playlists = {
        name: HLSPlaylist(
            vod_playlist_path = src_dir / chan / f"{res}.m3u8",
            output_dir = base_dir / chan,
            res=res,
            window_count=window_count,
            start_date_time=start_date_time,
            dry_run=dry_run,
        )
        for name, (chan, res) in channels.items()
    }

    processes = []
    for channel, playlist in playlists.items():
        print(f"starting channel {channel}...")
        p = Process(target=run_playlist, args=(playlist,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
